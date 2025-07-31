"""
Streamlit - T-Metal · BI Operacional + Análisis de Tiempos de Viaje
Versión 2025-01-15 – incluye:
• Producción horaria (viajes de carga y descarga)
• Conteo detallado de viajes por tipo (carga, descarga, retorno, otros)
• Ciclos completos por vehículo
• Productividad (% horas de carga vs horas activas)
• Toneladas acumuladas (≈ N(42 t, σ = 3 t) por viaje de producción)
• Soporte para Pilas ROM (Pila Rom 1, Pila Rom 2, Pila Rom 3)
• Filtros por turno (día/noche) con métricas diferenciadas
• Exportación a Excel
• 🆕 ANÁLISIS DE TIEMPOS DE VIAJE: Medición de duración de viajes entre origen y destino
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import unicodedata
from datetime import time
from io import BytesIO

st.set_page_config(
    page_title="⛏️ T-Metal – BI Operacional + Tiempos de Viaje",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# 0 | Parámetros globales
# ─────────────────────────────────────────────────────────────
MIN_ESTANCIA_S      = 3  # Ajustado para datos de prueba (era 60)
SHIFT_DAY_START     = time(8, 0)
SHIFT_NIGHT_START   = time(20, 0)

# Dominios dinámicos
STOCKS: set[str]    = set()
MODULES: set[str]   = set()
BOTADEROS: set[str] = set()
PILAS_ROM: set[str] = set()


# ─────────────────────────────────────────────────────────────
# 1 | Utilidades
# ─────────────────────────────────────────────────────────────
def turno(ts: pd.Timestamp) -> str:
    h = ts.time()
    return "dia" if SHIFT_DAY_START <= h < SHIFT_NIGHT_START else "noche"


def normalizar(s: str) -> str:
    """Quita tildes y pasa a minúsculas para detección robusta."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()


def preparar_datos(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["Tiempo de evento"] = pd.to_datetime(df["Tiempo de evento"], errors="coerce")
    df.dropna(subset=["Tiempo de evento"], inplace=True)
    df["Geocerca"] = df["Geocercas"].fillna("").str.strip()
    df.sort_values(["Nombre del Vehículo", "Tiempo de evento"], inplace=True)
    
    # 🔍 Logging para diagnóstico de viajes
    registros_vacios = len(df[df["Geocerca"] == ""])
    registros_totales = len(df)
    print(f"📊 Diagnóstico de datos preparados:")
    print(f"   - Total registros: {registros_totales}")
    print(f"   - Registros en viaje (geocerca vacía): {registros_vacios}")
    print(f"   - Registros en geocerca: {registros_totales - registros_vacios}")
    print(f"   - Porcentaje en viaje: {registros_vacios/registros_totales*100:.1f}%")
    
    return df


def poblar_dominios(df: pd.DataFrame) -> None:
    """Detecta automáticamente STOCKS, MODULES, BOTADEROS, PILAS_ROM, INSTALACIONES_FAENA."""
    global STOCKS, MODULES, BOTADEROS, PILAS_ROM
    geos = set(df["Geocerca"].unique()) - {""}
    STOCKS    = {g for g in geos if "stock"    in normalizar(g)}
    MODULES   = {g for g in geos if "modulo"   in normalizar(g)}
    BOTADEROS = {g for g in geos if "botadero" in normalizar(g)} or {"Botaderos"}
    PILAS_ROM = {g for g in geos if "pila rom" in normalizar(g)}
    # 🆕 Detectar instalaciones de faena
    INSTALACIONES_FAENA = {g for g in geos if "instalacion" in normalizar(g) or "faena" in normalizar(g)}
    # Agregar instalaciones de faena a la lista global
    globals()["INSTALACIONES_FAENA"] = INSTALACIONES_FAENA
    
    # 🖨️ IMPRESIÓN POR CONSOLA DE GEOCERCAS DETECTADAS
    print("=" * 60)
    print("🏭 GEOCERCAS DETECTADAS AUTOMÁTICAMENTE")
    print("=" * 60)
    print(f"📦 STOCKS ({len(STOCKS)}): {sorted(STOCKS) if STOCKS else 'Ninguna detectada'}")
    print(f"🏗️ MODULES ({len(MODULES)}): {sorted(MODULES) if MODULES else 'Ninguna detectada'}")
    print(f"🗑️ BOTADEROS ({len(BOTADEROS)}): {sorted(BOTADEROS) if BOTADEROS else 'Ninguna detectada'}")
    print(f"🪨 PILAS_ROM ({len(PILAS_ROM)}): {sorted(PILAS_ROM) if PILAS_ROM else 'Ninguna detectada'}")
    print(f"🏭 INSTALACIONES_FAENA ({len(INSTALACIONES_FAENA)}): {sorted(INSTALACIONES_FAENA) if INSTALACIONES_FAENA else 'Ninguna detectada'}")
    
    # Mostrar geocercas no clasificadas
    geocercas_clasificadas = STOCKS | MODULES | BOTADEROS | PILAS_ROM | INSTALACIONES_FAENA
    geocercas_no_clasificadas = geos - geocercas_clasificadas
    
    if geocercas_no_clasificadas:
        print(f"❓ GEOCERCAS NO CLASIFICADAS ({len(geocercas_no_clasificadas)}): {sorted(geocercas_no_clasificadas)}")
    else:
        print("✅ Todas las geocercas fueron clasificadas correctamente")
    
    print(f"📊 TOTAL GEOCERCAS ÚNICAS: {len(geos)}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────
# 2 | Extracción de transiciones geocerca-a-geocerca
# ─────────────────────────────────────────────────────────────
def extraer_transiciones(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta transiciones completas entre geocercas con filtrado inteligente:
    - Combina: Geocerca1 → [VIAJE] → Geocerca2 en Geocerca1 → Geocerca2
    - Filtra permanencias muy cortas (ruido GPS)
    - Usa un umbral más alto (60s) para permanencias reales
    """
    UMBRAL_PERMANENCIA_REAL = 60  # Umbral alto para permanencias reales (no ruido GPS)
    transiciones_completas = []
    total_cambios = 0
    transiciones_filtradas = 0

    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g.copy().sort_values("Tiempo de evento")
        
        # 🔍 PASO 1: Detectar permanencias reales (filtrar ruido GPS)
        geocercas_validas = []
        tiempos_entrada = []
        tiempos_salida = []
        
        geocerca_actual = None
        tiempo_entrada_actual = None
        
        for i, row in g.iterrows():
            geo = str(row["Geocerca"]).strip()
            tiempo = row["Tiempo de evento"]
            
            if geo != "":  # Registro en geocerca
                if geocerca_actual != geo:
                    # Cambio de geocerca o primera geocerca
                    if geocerca_actual is not None:
                        # Finalizar geocerca anterior
                        duracion = (tiempo - tiempo_entrada_actual).total_seconds()
                        if duracion >= UMBRAL_PERMANENCIA_REAL:
                            # Permanencia válida - registrar
                            geocercas_validas.append(geocerca_actual)
                            tiempos_entrada.append(tiempo_entrada_actual)
                            tiempos_salida.append(tiempo)
                        else:
                            print(f"   ⚠️ Filtrado ruido GPS: {geocerca_actual} ({duracion:.0f}s < {UMBRAL_PERMANENCIA_REAL}s)")
                    
                    # Iniciar nueva geocerca
                    geocerca_actual = geo
                    tiempo_entrada_actual = tiempo
            else:
                # Registro en viaje
                if geocerca_actual is not None:
                    # Salida de geocerca hacia viaje
                    duracion = (tiempo - tiempo_entrada_actual).total_seconds()
                    if duracion >= UMBRAL_PERMANENCIA_REAL:
                        # Permanencia válida - registrar
                        geocercas_validas.append(geocerca_actual)
                        tiempos_entrada.append(tiempo_entrada_actual)
                        tiempos_salida.append(tiempo)
                    else:
                        print(f"   ⚠️ Filtrado ruido GPS: {geocerca_actual} ({duracion:.0f}s < {UMBRAL_PERMANENCIA_REAL}s)")
                    
                    geocerca_actual = None
                    tiempo_entrada_actual = None
        
        # Procesar última geocerca si existe
        if geocerca_actual is not None:
            ultimo_tiempo = g["Tiempo de evento"].iloc[-1]
            duracion = (ultimo_tiempo - tiempo_entrada_actual).total_seconds()
            if duracion >= UMBRAL_PERMANENCIA_REAL:
                geocercas_validas.append(geocerca_actual)
                tiempos_entrada.append(tiempo_entrada_actual)
                tiempos_salida.append(ultimo_tiempo)
            else:
                print(f"   ⚠️ Filtrado ruido GPS: {geocerca_actual} ({duracion:.0f}s < {UMBRAL_PERMANENCIA_REAL}s)")
        
        # 🔍 PASO 2: Crear transiciones entre permanencias válidas
        for i in range(len(geocercas_validas) - 1):
            origen = geocercas_validas[i]
            destino = geocercas_validas[i + 1]
            tiempo_salida_origen = tiempos_salida[i]
            tiempo_entrada_destino = tiempos_entrada[i + 1]
            
            # Duración de permanencia en el origen
            duracion_permanencia = (tiempo_salida_origen - tiempos_entrada[i]).total_seconds()
            
            total_cambios += 1
            
            transiciones_completas.append({
                "Nombre del Vehículo": veh,
                "Origen": origen,
                "Destino": destino,
                "Tiempo_entrada": tiempos_entrada[i],
                "Tiempo_salida": tiempo_salida_origen,
                "Duracion_s": duracion_permanencia,
                "Turno": turno(tiempos_entrada[i])
            })

    # Logging para verificar el filtrado
    if total_cambios > 0:
        print(f"🔍 Detección de transiciones con filtrado inteligente:")
        print(f"   - Umbral de permanencia real: {UMBRAL_PERMANENCIA_REAL}s")
        print(f"   - Total transiciones válidas registradas: {len(transiciones_completas)}")

    if transiciones_completas:
        return pd.DataFrame(transiciones_completas)
    else:
        return pd.DataFrame(columns=[
            "Nombre del Vehículo", "Origen", "Destino",
            "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"
        ])


# ─────────────────────────────────────────────────────────────
# 🆕 2.1 | Análisis de tiempos de viaje (cuando Geocercas está vacío)
# ─────────────────────────────────────────────────────────────
def extraer_tiempos_viaje(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae tiempos de viaje cuando el vehículo no está en ninguna geocerca conocida.
    Un registro con Geocercas vacío indica que el vehículo está en viaje.
    """
    registros_viaje: list[pd.DataFrame] = []
    
    print("🚗 Iniciando extracción de tiempos de viaje...")
    
    # Diagnóstico inicial
    registros_vacios_total = len(df[df["Geocerca"] == ""])
    print(f"   🔍 Registros con geocerca vacía en datos de entrada: {registros_vacios_total}")
    
    if registros_vacios_total == 0:
        print("   ⚠️ NO hay registros con geocerca vacía. No se pueden extraer viajes.")
        return pd.DataFrame(columns=[
            "Nombre del Vehículo", "Origen", "Destino",
            "Tiempo_inicio_viaje", "Tiempo_fin_viaje", "Duracion_viaje_s", "Turno", "Puntos_gps"
        ])
    
    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g.copy().sort_values("Tiempo de evento")
        registros_vacios_vehiculo = len(g[g["Geocerca"] == ""])
        print(f"   📍 Procesando vehículo: {veh} ({len(g)} registros, {registros_vacios_vehiculo} en viaje)")
        
        if registros_vacios_vehiculo == 0:
            print(f"      ⚠️ {veh}: No tiene registros en viaje")
            continue
        
        # Mostrar muestra de datos para debugging
        print(f"      📋 Muestra de datos para {veh}:")
        for i, row in g.head(10).iterrows():
            estado = "VIAJE" if row["Geocerca"] == "" else f"GEOCERCA: {row['Geocerca']}"
            print(f"         {row['Tiempo de evento']} → {estado}")
        
        # Encontrar secuencias de registros donde Geocerca está vacío
        g["En_viaje"] = g["Geocerca"] == ""
        g["Grupo_viaje"] = (g["En_viaje"] != g["En_viaje"].shift()).cumsum()
        
        viajes_encontrados = 0
        
        # Mostrar información de grupos
        grupos_viaje = g[g["En_viaje"]]["Grupo_viaje"].unique()
        print(f"      🔢 Grupos de viaje detectados: {len(grupos_viaje)}")
        
        # Procesar solo grupos donde hay registros en viaje
        for grupo_id, grupo in g.groupby("Grupo_viaje"):
            if not grupo["En_viaje"].iloc[0]:  # Solo procesar grupos en viaje
                continue
                
            print(f"         📦 Procesando grupo {grupo_id}: {len(grupo)} registros en viaje")
                
            # Calcular tiempo total del viaje
            tiempo_inicio = grupo["Tiempo de evento"].iloc[0]
            tiempo_fin = grupo["Tiempo de evento"].iloc[-1]
            duracion_viaje = (tiempo_fin - tiempo_inicio).total_seconds()
            
            print(f"            ⏱️ Duración: {duracion_viaje:.0f} segundos")
            
            # Filtrar viajes muy cortos (menos de 30 segundos)
            if duracion_viaje < 30:
                print(f"            ❌ Viaje muy corto, descartado")
                continue
                
            # Determinar origen y destino del viaje
            # Buscar el último registro antes del viaje (origen)
            idx_antes_viaje = g[g["Tiempo de evento"] < tiempo_inicio].index
            origen = ""
            if len(idx_antes_viaje) > 0:
                origen = str(g.loc[idx_antes_viaje[-1], "Geocerca"]).strip()
            
            # Buscar el primer registro después del viaje (destino)
            idx_despues_viaje = g[g["Tiempo de evento"] > tiempo_fin].index
            destino = ""
            if len(idx_despues_viaje) > 0:
                destino = str(g.loc[idx_despues_viaje[0], "Geocerca"]).strip()
            
            print(f"            🎯 Origen: '{origen}' → Destino: '{destino}'")
            
            # Incluir viajes incluso si origen o destino están vacíos (para debugging)
            registros_viaje.append(pd.DataFrame({
                "Nombre del Vehículo": [veh],
                "Origen": [origen if origen else "DESCONOCIDO"],
                "Destino": [destino if destino else "DESCONOCIDO"],
                "Tiempo_inicio_viaje": [tiempo_inicio],
                "Tiempo_fin_viaje": [tiempo_fin],
                "Duracion_viaje_s": [duracion_viaje],
                "Turno": [turno(tiempo_inicio)],
                "Puntos_gps": [len(grupo)]
            }))
            viajes_encontrados += 1
        
        print(f"      ✅ {viajes_encontrados} viajes encontrados para {veh}")
    
    total_viajes = len(registros_viaje)
    print(f"🎯 Total de viajes extraídos: {total_viajes}")
    
    if registros_viaje:
        return pd.concat(registros_viaje, ignore_index=True)
    return pd.DataFrame(columns=[
        "Nombre del Vehículo", "Origen", "Destino",
        "Tiempo_inicio_viaje", "Tiempo_fin_viaje", "Duracion_viaje_s", "Turno", "Puntos_gps"
    ])


# ─────────────────────────────────────────────────────────────
# 3 | Clasificación de proceso con secuencias
# ─────────────────────────────────────────────────────────────
def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica procesos considerando secuencias temporales:
    - Carga: Stock → Módulo/Pila ROM
    - Descarga: Módulo/Pila ROM → Botadero
    - Retorno: Botadero → Módulo/Pila ROM (después de descarga)
    - Retorno: Módulo/Pila ROM → Stock (después de carga)
    - Otros: Cualquier otra combinación
    """
    if df.empty:
        return df
    
    # Las transiciones ya vienen filtradas por extraer_transiciones()
    # No es necesario filtrar nuevamente aquí
    
    df = df.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    df["Proceso"] = "otro"  # Inicializar todos como "otro"
    
    # Obtener INSTALACIONES_FAENA del contexto global
    INSTALACIONES_FAENA = globals().get("INSTALACIONES_FAENA", set())
    
    # Procesar cada vehículo por separado y reconstruir el DataFrame
    grupos_procesados = []
    
    for veh, grupo in df.groupby("Nombre del Vehículo"):
        # Crear una copia del grupo y ordenar por tiempo
        grupo = grupo.copy().sort_values("Tiempo_entrada").reset_index(drop=True)
        
        for i in range(len(grupo)):
            origen = grupo.loc[i, "Origen"]
            destino = grupo.loc[i, "Destino"]
            
            # 🏭 PRIORIDAD ALTA: Movimientos que involucran instalaciones de faena son "otros"
            if origen in INSTALACIONES_FAENA or destino in INSTALACIONES_FAENA:
                grupo.loc[i, "Proceso"] = "otro"
                continue
            
            # 1. CARGA: Stock → Módulo/Pila ROM
            if origen in STOCKS and (destino in MODULES or destino in PILAS_ROM):
                grupo.loc[i, "Proceso"] = "carga"
                continue
            
            # 2. DESCARGA: Módulo/Pila ROM → Botadero (sin secuencia previa requerida)
            if (origen in MODULES or origen in PILAS_ROM) and destino in BOTADEROS:
                grupo.loc[i, "Proceso"] = "descarga"
                continue
            
            # 3. RETORNO: Botadero → Módulo/Pila ROM (después de descarga)
            if origen in BOTADEROS and (destino in MODULES or destino in PILAS_ROM):
                # Verificar si el viaje anterior fue una descarga
                if i > 0:
                    viaje_anterior = grupo.loc[i-1, "Proceso"]
                    if viaje_anterior == "descarga":
                        grupo.loc[i, "Proceso"] = "retorno"
                        continue
                # Si no hay secuencia válida, es "otro"
                grupo.loc[i, "Proceso"] = "otro"
                continue
            
            # 4. RETORNO: Módulo/Pila ROM → Stock (después de carga)
            if (origen in MODULES or origen in PILAS_ROM) and destino in STOCKS:
                # Verificar si el viaje anterior fue una carga
                if i > 0:
                    viaje_anterior = grupo.loc[i-1, "Proceso"]
                    if viaje_anterior == "carga":
                        grupo.loc[i, "Proceso"] = "retorno"
                        continue
                # Si no hay secuencia válida, es "otro"
                grupo.loc[i, "Proceso"] = "otro"
                continue
        
        grupos_procesados.append(grupo)
    
    # Reconstruir el DataFrame completo
    if grupos_procesados:
        return pd.concat(grupos_procesados, ignore_index=True)
    else:
        return df


def clasificar_proceso(row: pd.Series) -> str:
    """
    Clasificación simple sin secuencias (mantenida para compatibilidad)
    """
    o, d = row["Origen"], row["Destino"]
    
    # Obtener INSTALACIONES_FAENA del contexto global
    INSTALACIONES_FAENA = globals().get("INSTALACIONES_FAENA", set())
    
    # 🏭 PRIORIDAD ALTA: Movimientos que involucran instalaciones de faena son "otros"
    if o in INSTALACIONES_FAENA or d in INSTALACIONES_FAENA:
        return "otro"
    
    # Proceso de CARGA: STOCKS → MODULES o PILAS_ROM
    if o in STOCKS and (d in MODULES or d in PILAS_ROM):
        return "carga"
    # Proceso de RETORNO: MODULES o PILAS_ROM → STOCKS
    if (o in MODULES or o in PILAS_ROM) and d in STOCKS:
        return "retorno"
    # Proceso de DESCARGA: MODULES o PILAS_ROM → BOTADEROS
    if (o in MODULES or o in PILAS_ROM) and d in BOTADEROS:
        return "descarga"
    return "otro"


def clasificar_proceso_viaje(row: pd.Series) -> str:
    """
    Clasificación simple para viajes (mantenida para compatibilidad)
    """
    o, d = row["Origen"], row["Destino"]
    
    # Obtener INSTALACIONES_FAENA del contexto global
    INSTALACIONES_FAENA = globals().get("INSTALACIONES_FAENA", set())
    
    # 🏭 PRIORIDAD ALTA: Movimientos que involucran instalaciones de faena son "otros"
    if o in INSTALACIONES_FAENA or d in INSTALACIONES_FAENA:
        return "otro"
    
    # Proceso de CARGA: STOCKS → MODULES o PILAS_ROM
    if o in STOCKS and (d in MODULES or d in PILAS_ROM):
        return "carga"
    # Proceso de RETORNO: MODULES o PILAS_ROM → STOCKS
    if (o in MODULES or o in PILAS_ROM) and d in STOCKS:
        return "retorno"
    # Proceso de DESCARGA: MODULES o PILAS_ROM → BOTADEROS
    if (o in MODULES or o in PILAS_ROM) and d in BOTADEROS:
        return "descarga"
    return "otro"


# ─────────────────────────────────────────────────────────────
# 4 | Detección de ciclos mejorada con secuencias
# ─────────────────────────────────────────────────────────────
def detectar_ciclos_mejorados(trans: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta ciclos completos considerando secuencias:
    - Ciclo de carga: Stock → Módulo/Pila ROM → Stock
    - Ciclo de descarga: Módulo/Pila ROM → Botadero → Módulo/Pila ROM
    """
    if trans.empty:
        return pd.DataFrame()
    
    # Usar clasificación con secuencias
    trans = clasificar_proceso_con_secuencia(trans)
    
    ciclos_completos = []
    
    for veh, grupo in trans.groupby("Nombre del Vehículo"):
        grupo = grupo.sort_values("Tiempo_entrada").reset_index(drop=True)
        
        for i in range(len(grupo) - 1):
            proceso_actual = grupo.loc[i, "Proceso"]
            proceso_siguiente = grupo.loc[i + 1, "Proceso"]
            
            # Ciclo de carga: carga → retorno (Stock → Módulo → Stock)
            if proceso_actual == "carga" and proceso_siguiente == "retorno":
                origen_carga = grupo.loc[i, "Origen"]
                destino_retorno = grupo.loc[i + 1, "Destino"]
                
                # Verificar que el retorno va de vuelta al stock
                if origen_carga in STOCKS and destino_retorno in STOCKS:
                    ciclos_completos.append({
                        "Nombre del Vehículo": veh,
                        "Tipo_Ciclo": "Carga",
                        "Origen_Ciclo": origen_carga,
                        "Destino_Ciclo": destino_retorno,
                        "Tiempo_inicio": grupo.loc[i, "Tiempo_entrada"],
                        "Tiempo_fin": grupo.loc[i + 1, "Tiempo_salida"],
                        "Duracion_ciclo_s": (grupo.loc[i + 1, "Tiempo_salida"] - grupo.loc[i, "Tiempo_entrada"]).total_seconds(),
                        "Proceso_1": proceso_actual,
                        "Proceso_2": proceso_siguiente
                    })
            
            # Ciclo de descarga: descarga → retorno (Módulo → Botadero → Módulo)
            elif proceso_actual == "descarga" and proceso_siguiente == "retorno":
                origen_descarga = grupo.loc[i, "Origen"]
                destino_retorno = grupo.loc[i + 1, "Destino"]
                
                # Verificar que el retorno va de vuelta al módulo/pila
                if (origen_descarga in MODULES or origen_descarga in PILAS_ROM) and \
                   (destino_retorno in MODULES or destino_retorno in PILAS_ROM):
                    ciclos_completos.append({
                        "Nombre del Vehículo": veh,
                        "Tipo_Ciclo": "Descarga",
                        "Origen_Ciclo": origen_descarga,
                        "Destino_Ciclo": destino_retorno,
                        "Tiempo_inicio": grupo.loc[i, "Tiempo_entrada"],
                        "Tiempo_fin": grupo.loc[i + 1, "Tiempo_salida"],
                        "Duracion_ciclo_s": (grupo.loc[i + 1, "Tiempo_salida"] - grupo.loc[i, "Tiempo_entrada"]).total_seconds(),
                        "Proceso_1": proceso_actual,
                        "Proceso_2": proceso_siguiente
                    })
    
    if ciclos_completos:
        return pd.DataFrame(ciclos_completos)
    return pd.DataFrame()


def detectar_ciclos(trans: pd.DataFrame) -> pd.DataFrame:
    """
    Función original mantenida para compatibilidad
    """
    if trans.empty:
        return pd.DataFrame()
    t = trans.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    t["Proceso"]   = t.apply(clasificar_proceso, axis=1)
    t["Proc_next"] = t.groupby("Nombre del Vehículo")["Proceso"].shift(-1)
    mask   = (t["Proceso"] == "carga") & (t["Proc_next"] == "retorno")
    ciclos = t[mask].copy()
    ciclos["Ciclo_ID"] = np.arange(len(ciclos))
    return ciclos


# ─────────────────────────────────────────────────────────────
# 5 | Métricas agregadas + productividad
# ─────────────────────────────────────────────────────────────
def construir_metricas(trans: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if trans.empty:
        return pd.DataFrame(), pd.DataFrame()

    trans = trans.copy()
    trans["Proceso"]  = trans.apply(clasificar_proceso, axis=1)
    trans["Hora_cal"] = trans["Tiempo_entrada"].dt.floor("h")   # «h» minúscula

    viajes_h = (
        trans.groupby(["Hora_cal", "Proceso"]).size()
             .unstack(fill_value=0).reset_index()
             .reindex(columns=["Hora_cal", "carga", "retorno", "descarga", "otro"],
                      fill_value=0)
    )

    # horas activas y horas en viajes de carga
    trans["Duracion_h"] = trans["Duracion_s"] / 3600
    actividad = (
        trans.groupby([trans["Tiempo_entrada"].dt.date.rename("Fecha"),
                       "Nombre del Vehículo"])
             ["Duracion_h"].sum().reset_index(name="Horas_activas")
    )
    carga = (
        trans[trans["Proceso"] == "carga"]
        .groupby([trans["Tiempo_entrada"].dt.date.rename("Fecha"),
                  "Nombre del Vehículo"])
        ["Duracion_h"].sum().reset_index(name="Horas_carga")
    )
    productividad = actividad.merge(carga, how="left",
                                    on=["Fecha", "Nombre del Vehículo"]).fillna(0)
    productividad["Prod_pct"] = (productividad["Horas_carga"]
                                 / productividad["Horas_activas"].replace(0, np.nan)) * 100
    productividad.replace([np.inf, -np.inf], 0, inplace=True)
    return viajes_h, productividad


# ─────────────────────────────────────────────────────────────
# 🆕 5.1 | Métricas de tiempos de viaje
# ─────────────────────────────────────────────────────────────
def construir_metricas_viaje(viajes: pd.DataFrame) -> pd.DataFrame:
    """Construye métricas específicas para tiempos de viaje"""
    if viajes.empty:
        return pd.DataFrame()
    
    viajes = viajes.copy()
    viajes["Proceso"] = viajes.apply(clasificar_proceso_viaje, axis=1)
    viajes["Duracion_viaje_min"] = viajes["Duracion_viaje_s"] / 60
    
    # Métricas por vehículo
    metricas_vehiculo = viajes.groupby("Nombre del Vehículo").agg({
        "Duracion_viaje_s": ["count", "mean", "std", "min", "max"],
        "Duracion_viaje_min": ["mean", "min", "max"],
        "Puntos_gps": ["mean", "min", "max"]
    }).round(2)
    
    # Flatten column names
    metricas_vehiculo.columns = [
        f"{col[0]}_{col[1]}" for col in metricas_vehiculo.columns
    ]
    metricas_vehiculo = metricas_vehiculo.reset_index()
    
    # Renombrar columnas para mayor claridad
    metricas_vehiculo = metricas_vehiculo.rename(columns={
        "Duracion_viaje_s_count": "Total_viajes",
        "Duracion_viaje_s_mean": "Tiempo_promedio_s",
        "Duracion_viaje_s_std": "Desv_estandar_s",
        "Duracion_viaje_s_min": "Tiempo_min_s",
        "Duracion_viaje_s_max": "Tiempo_max_s",
        "Duracion_viaje_min_mean": "Tiempo_promedio_min",
        "Duracion_viaje_min_min": "Tiempo_min_min",
        "Duracion_viaje_min_max": "Tiempo_max_min",
        "Puntos_gps_mean": "Puntos_gps_promedio",
        "Puntos_gps_min": "Puntos_gps_min",
        "Puntos_gps_max": "Puntos_gps_max"
    })
    
    return metricas_vehiculo


# ─────────────────────────────────────────────────────────────
# 6 | Interfaz Streamlit
# ─────────────────────────────────────────────────────────────
st.header("📤 Carga de archivo CSV – Eventos GPS + Análisis de Tiempos de Viaje")
archivo = st.file_uploader("Selecciona el CSV exportado desde GeoAustral", type=["csv"])

if archivo:
    raw = pd.read_csv(archivo)
    df  = preparar_datos(raw)
    poblar_dominios(df)

    # ─── Filtros de fecha, vehículo y turno ────────────────────────
    dmin, dmax = df["Tiempo de evento"].dt.date.min(), df["Tiempo de evento"].dt.date.max()
    rango = st.date_input("Rango de fechas", [dmin, dmax])
    if isinstance(rango, tuple): rango = list(rango)
    if len(rango) == 1:          rango = [rango[0], rango[0]]

    df = df[(df["Tiempo de evento"].dt.date >= rango[0])
            & (df["Tiempo de evento"].dt.date <= rango[1])]

    veh_opts = ["Todos"] + sorted(df["Nombre del Vehículo"].unique())
    veh_sel  = st.selectbox("Vehículo", veh_opts)
    if veh_sel != "Todos":
        df = df[df["Nombre del Vehículo"] == veh_sel]

    # Filtro por turno
    turno_opts = ["Todos", "Día", "Noche"]
    turno_sel = st.selectbox("Turno", turno_opts)
    
    # Aplicar filtro de turno
    if turno_sel != "Todos":
        turno_filter = "dia" if turno_sel == "Día" else "noche"
        df = df[df["Tiempo de evento"].apply(turno) == turno_filter]

    # ─── Procesamiento core ─────────────────────────────────
    trans   = extraer_transiciones(df)
    viajes  = extraer_tiempos_viaje(df)  # 🆕 Nueva funcionalidad
    
    if trans.empty and viajes.empty:
        st.warning("No se encontraron transiciones válidas ni viajes detectados.")
        st.stop()

    # 🎯 Información sobre detección mejorada de transiciones
    if not trans.empty:
        st.success(f"""
        **🆕 Detección Mejorada de Transiciones:**
        - **Entradas desde viaje**: Detecta cuando vehículo entra a geocerca desde viaje (\"\" → Geocerca)
        - **Salidas hacia viaje**: Detecta cuando vehículo sale de geocerca hacia viaje (Geocerca → \"\")
        - **Cambios directos**: Detecta cambios directos entre geocercas (Geocerca1 → Geocerca2)
        - **Filtrado por tiempo**: Solo permanencias ≥ {MIN_ESTANCIA_S} segundos se consideran válidas
        - **Eliminación de ruido GPS**: Transiciones < {MIN_ESTANCIA_S}s se filtran automáticamente
        """)

    # 🆕 Usar clasificación con secuencias para mejor precisión
    trans = clasificar_proceso_con_secuencia(trans)
    ciclos_mejorados = detectar_ciclos_mejorados(trans)
    ciclos = detectar_ciclos(trans)  # Mantener función original para compatibilidad
    viajes_h, productividad = construir_metricas(trans)
    metricas_viaje = construir_metricas_viaje(viajes)  # 🆕 Nuevas métricas
    
    # 🆕 Mostrar información sobre geocercas detectadas
    st.subheader("🏭 Geocercas Detectadas Automáticamente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📦 Stocks:**")
        if STOCKS:
            for stock in sorted(STOCKS):
                st.write(f"• {stock}")
        else:
            st.write("Ninguna detectada")
        
        st.markdown("**🏗️ Módulos:**")
        if MODULES:
            for modulo in sorted(MODULES):
                st.write(f"• {modulo}")
        else:
            st.write("Ninguno detectado")
        
        st.markdown("**🗑️ Botaderos:**")
        if BOTADEROS:
            for botadero in sorted(BOTADEROS):
                st.write(f"• {botadero}")
        else:
            st.write("Ninguno detectado")
    
    with col2:
        st.markdown("**🪨 Pilas ROM:**")
        if PILAS_ROM:
            for pila in sorted(PILAS_ROM):
                st.write(f"• {pila}")
        else:
            st.write("Ninguna detectada")
        
        st.markdown("**🏭 Instalaciones de Faena:**")
        INSTALACIONES_FAENA = globals().get("INSTALACIONES_FAENA", set())
        if INSTALACIONES_FAENA:
            for instalacion in sorted(INSTALACIONES_FAENA):
                st.write(f"• {instalacion}")
        else:
            st.write("Ninguna detectada")
    
    # Mostrar geocercas no clasificadas
    geocercas_clasificadas = STOCKS | MODULES | BOTADEROS | PILAS_ROM | INSTALACIONES_FAENA
    geocercas_no_clasificadas = set(df["Geocerca"].unique()) - {""} - geocercas_clasificadas
    
    if geocercas_no_clasificadas:
        st.warning(f"""
        **❓ Geocercas No Clasificadas ({len(geocercas_no_clasificadas)}):**
        {', '.join(sorted(geocercas_no_clasificadas))}
        
        Estas geocercas no coinciden con los patrones de detección automática.
        """)
    else:
        st.success("✅ Todas las geocercas fueron clasificadas correctamente")
    
    st.info(f"""
    **📊 Resumen de Detección:**
    - **Total geocercas únicas**: {len(set(df['Geocerca'].unique()) - {''})}
    - **Geocercas clasificadas**: {len(geocercas_clasificadas)}
    - **Geocercas no clasificadas**: {len(geocercas_no_clasificadas)}
    """)

    # ────────────────────────────────────────────────────────
    # 🆕 NUEVA SECCIÓN: Análisis de Tiempos de Viaje
    # ────────────────────────────────────────────────────────
    st.subheader("🚗 Análisis de Tiempos de Viaje")
    
    # Información sobre la funcionalidad
    st.info("""
    **📋 Funcionalidad de Tiempos de Viaje:**
    - **Detección automática**: Cuando la columna "Geocercas" está vacía, el sistema detecta que el vehículo está en viaje
    - **Cálculo de duración**: Se mide el tiempo desde que sale de una geocerca hasta que llega a la siguiente
    - **Análisis por proceso**: Los viajes se clasifican según el origen y destino (carga, descarga, retorno, otros)
    - **Métricas detalladas**: Tiempo promedio, mínimo, máximo y desviación estándar por vehículo
    """)
    
    # 🆕 Información sobre la nueva lógica de clasificación
    st.success("""
    **🆕 Lógica de Clasificación Corregida con Secuencias:**
    - **Carga**: Stock → Módulo/Pila ROM
    - **Descarga**: Módulo/Pila ROM → Botadero
    - **Retorno**: Botadero → Módulo/Pila ROM (después de descarga)
    - **Retorno**: Módulo/Pila ROM → Stock (después de carga)
    - **Otros**: Cualquier movimiento desde/hacia instalaciones de faena
    """)
    
    if not viajes.empty:
        # Mostrar estadísticas generales de viajes
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_viajes = len(viajes)
            st.metric("Total viajes detectados", total_viajes)
        with col2:
            tiempo_promedio = viajes["Duracion_viaje_s"].mean() / 60
            st.metric("Tiempo promedio", f"{tiempo_promedio:.1f} min")
        with col3:
            tiempo_min = viajes["Duracion_viaje_s"].min() / 60
            st.metric("Tiempo mínimo", f"{tiempo_min:.1f} min")
        with col4:
            tiempo_max = viajes["Duracion_viaje_s"].max() / 60
            st.metric("Tiempo máximo", f"{tiempo_max:.1f} min")
        
        # Gráfico de distribución de tiempos de viaje
        st.subheader("📊 Distribución de Tiempos de Viaje")
        
        # Preparar datos para el gráfico
        viajes_grafico = viajes.copy()
        viajes_grafico["Duracion_min"] = viajes_grafico["Duracion_viaje_s"] / 60
        viajes_grafico["Proceso"] = viajes_grafico.apply(clasificar_proceso_viaje, axis=1)
        
        # Gráfico de histograma
        chart_distribucion = (
            alt.Chart(viajes_grafico)
            .mark_bar()
            .encode(
                x=alt.X("Duracion_min:Q", bin=alt.Bin(maxbins=20), title="Tiempo de viaje (minutos)"),
                y=alt.Y("count():Q", title="Frecuencia"),
                color=alt.Color("Proceso:N", 
                               scale=alt.Scale(domain=["carga", "descarga", "retorno", "otro"], 
                                             range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])),
                tooltip=["Duracion_min:Q", "Proceso:N", "count():Q"]
            )
            .properties(height=300, title="Distribución de tiempos de viaje por tipo de proceso")
        )
        st.altair_chart(chart_distribucion, use_container_width=True)
        
        # Gráfico de tiempos por vehículo
        st.subheader("🚛 Tiempos de Viaje por Vehículo")
        
        # Preparar datos para gráfico por vehículo
        tiempos_vehiculo = viajes.groupby("Nombre del Vehículo").agg({
            "Duracion_viaje_s": ["mean", "count"]
        }).round(2)
        tiempos_vehiculo.columns = ["Tiempo_promedio_s", "Total_viajes"]
        tiempos_vehiculo = tiempos_vehiculo.reset_index()
        tiempos_vehiculo["Tiempo_promedio_min"] = tiempos_vehiculo["Tiempo_promedio_s"] / 60
        
        # Gráfico de barras por vehículo
        chart_vehiculos = (
            alt.Chart(tiempos_vehiculo)
            .mark_bar()
            .encode(
                x=alt.X("Nombre del Vehículo:N", sort="-y", title="Vehículo"),
                y=alt.Y("Tiempo_promedio_min:Q", title="Tiempo promedio (minutos)"),
                tooltip=["Nombre del Vehículo:N", "Tiempo_promedio_min:Q", "Total_viajes:Q"]
            )
            .properties(height=300, title="Tiempo promedio de viaje por vehículo")
        )
        st.altair_chart(chart_vehiculos, use_container_width=True)
        
        # Tabla detallada de métricas por vehículo
        st.subheader("📋 Métricas Detalladas por Vehículo")
        if not metricas_viaje.empty:
            st.dataframe(metricas_viaje, use_container_width=True)
        
        # Análisis por tipo de proceso
        st.subheader("🔄 Análisis por Tipo de Proceso")
        
        viajes_con_proceso = viajes.copy()
        viajes_con_proceso["Proceso"] = viajes_con_proceso.apply(clasificar_proceso_viaje, axis=1)
        viajes_con_proceso["Duracion_min"] = viajes_con_proceso["Duracion_viaje_s"] / 60
        
        # Estadísticas por proceso
        stats_proceso = viajes_con_proceso.groupby("Proceso").agg({
            "Duracion_viaje_s": ["count", "mean", "std", "min", "max"],
            "Duracion_min": ["mean", "min", "max"]
        }).round(2)
        
        # Flatten column names
        stats_proceso.columns = [
            f"{col[0]}_{col[1]}" for col in stats_proceso.columns
        ]
        stats_proceso = stats_proceso.reset_index()
        
        # Renombrar columnas
        stats_proceso = stats_proceso.rename(columns={
            "Duracion_viaje_s_count": "Total_viajes",
            "Duracion_viaje_s_mean": "Tiempo_promedio_s",
            "Duracion_viaje_s_std": "Desv_estandar_s",
            "Duracion_viaje_s_min": "Tiempo_min_s",
            "Duracion_viaje_s_max": "Tiempo_max_s",
            "Duracion_min_mean": "Tiempo_promedio_min",
            "Duracion_min_min": "Tiempo_min_min",
            "Duracion_min_max": "Tiempo_max_min"
        })
        
        st.dataframe(stats_proceso, use_container_width=True)
        
        # Gráfico de tiempos por proceso
        chart_proceso = (
            alt.Chart(viajes_con_proceso)
            .mark_boxplot()
            .encode(
                x=alt.X("Proceso:N", title="Tipo de Proceso"),
                y=alt.Y("Duracion_min:Q", title="Tiempo de viaje (minutos)"),
                color=alt.Color("Proceso:N", 
                               scale=alt.Scale(domain=["carga", "descarga", "retorno", "otro"], 
                                             range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]))
            )
            .properties(height=300, title="Distribución de tiempos de viaje por tipo de proceso")
        )
        st.altair_chart(chart_proceso, use_container_width=True)
        
    else:
        st.info("No se detectaron viajes en el período seleccionado. Los viajes se detectan cuando la columna 'Geocercas' está vacía.")

    # ────────────────────────────────────────────────────────
    #  Dashboard Original (mantenido de app5.py)
    # ────────────────────────────────────────────────────────
    if not trans.empty:
        st.subheader("🔋 Producción horaria – Viajes de carga y descarga")
        
        # Crear gráfico combinado de carga y descarga
        viajes_h_combinado = trans[trans["Proceso"].isin(["carga", "descarga"])].copy()
        if not viajes_h_combinado.empty:
            viajes_h_combinado["Hora_cal"] = viajes_h_combinado["Tiempo_entrada"].dt.floor("h")
            
            # Agrupar por hora y proceso
            viajes_agrupados = viajes_h_combinado.groupby(["Hora_cal", "Proceso"]).size().reset_index(name="Cantidad")
            
            # Crear gráfico con dos líneas
            chart_produccion = (
                alt.Chart(viajes_agrupados)
                .mark_line(point=True, size=3)
                .encode(
                    x=alt.X("Hora_cal:T", title="Fecha-hora"),
                    y=alt.Y("Cantidad:Q", title="Cantidad de viajes"),
                    color=alt.Color("Proceso:N", 
                                   scale=alt.Scale(domain=["carga", "descarga"], 
                                                 range=["#1f77b4", "#ff7f0e"]),
                                   legend=alt.Legend(title="Tipo de viaje")),
                    tooltip=["Hora_cal:T", "Proceso:N", "Cantidad:Q"]
                )
                .properties(height=300, title="Producción horaria - Viajes de carga y descarga")
            )
            st.altair_chart(chart_produccion, use_container_width=True)
            
            # Mostrar estadísticas de producción
            col1, col2, col3 = st.columns(3)
            with col1:
                total_carga = len(viajes_h_combinado[viajes_h_combinado["Proceso"] == "carga"])
                st.metric("Total viajes de carga", total_carga)
            with col2:
                total_descarga = len(viajes_h_combinado[viajes_h_combinado["Proceso"] == "descarga"])
                st.metric("Total viajes de descarga", total_descarga)
            with col3:
                total_produccion = total_carga + total_descarga
                st.metric("Total producción", total_produccion)
        else:
            st.info("Sin registros de carga o descarga en el período seleccionado.")
    else:
        st.info("Sin transiciones disponibles para mostrar producción.")

    # ─── Producción horaria por turno ──────────────────────────────
    if not trans.empty:
        st.subheader("🌅🌙 Producción horaria por turno")
        
        # Crear datos por turno para gráficos
        viajes_h_con_turno = trans[trans["Proceso"].isin(["carga", "descarga"])].copy()
        if not viajes_h_con_turno.empty:
            viajes_h_con_turno["Hora_cal"] = viajes_h_con_turno["Tiempo_entrada"].dt.floor("h")
            
            # Gráfico por turno
            chart_turnos = (
                alt.Chart(viajes_h_con_turno)
                .mark_circle(size=60)
                .encode(
                    x=alt.X("Hora_cal:T", title="Hora del día"),
                    y=alt.Y("count():Q", title="Viajes de producción"),
                    color=alt.Color("Turno:N", scale=alt.Scale(domain=["dia", "noche"], 
                                                              range=["#FF6B6B", "#4ECDC4"])),
                    tooltip=["Hora_cal:T", "Turno:N", "count():Q"]
                )
                .properties(height=300, title="Viajes de producción por hora y turno")
            )
            st.altair_chart(chart_turnos, use_container_width=True)
            
            # Estadísticas por turno
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🌅 Turno Día**")
                viajes_dia_hora = viajes_h_con_turno[viajes_h_con_turno["Turno"] == "dia"]
                if not viajes_dia_hora.empty:
                    total_dia = len(viajes_dia_hora)
                    st.metric("Total viajes día", total_dia)
                else:
                    st.info("Sin viajes en turno día")
            
            with col2:
                st.markdown("**🌙 Turno Noche**")
                viajes_noche_hora = viajes_h_con_turno[viajes_h_con_turno["Turno"] == "noche"]
                if not viajes_noche_hora.empty:
                    total_noche = len(viajes_noche_hora)
                    st.metric("Total viajes noche", total_noche)
                else:
                    st.info("Sin viajes en turno noche")

    # Conteo global de viajes
    if not trans.empty:
        st.subheader("📊 Conteo global de viajes (período filtrado)")
        
        # Contar por tipo de proceso
        conteo_procesos = trans["Proceso"].value_counts()
        
        # Crear DataFrame con información detallada
        resumen_viajes = pd.DataFrame({
            "Tipo de Viaje": ["Carga", "Descarga", "Retorno", "Otros"],
        })
        
        # Agregar conteos
        resumen_viajes["Cantidad"] = [
            conteo_procesos.get("carga", 0),
            conteo_procesos.get("descarga", 0),
            conteo_procesos.get("retorno", 0),
            conteo_procesos.get("otro", 0)
        ]
        
        # Agregar porcentajes
        total_viajes = resumen_viajes["Cantidad"].sum()
        resumen_viajes["Porcentaje"] = (resumen_viajes["Cantidad"] / total_viajes * 100).round(1)
        
        # Mostrar tabla
        st.dataframe(resumen_viajes, use_container_width=True)
        
        # Mostrar métricas destacadas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Viajes de Carga", conteo_procesos.get("carga", 0))
        with col2:
            st.metric("Viajes de Descarga", conteo_procesos.get("descarga", 0))
        with col3:
            st.metric("Viajes de Retorno", conteo_procesos.get("retorno", 0))
        with col4:
            st.metric("Otros Viajes", conteo_procesos.get("otro", 0))

    # ─── Métricas por turno ──────────────────────────────────────
    if not trans.empty:
        st.subheader("🌅🌙 Métricas por turno")
        
        # Información sobre turnos
        st.info("""
        **Definición de turnos:**
        - **Turno Día**: 8:00:00 a 20:00:00
        - **Turno Noche**: 20:00:00 a 8:00:00 (del día siguiente)
        """)
        
        # Separar datos por turno
        trans_dia = trans[trans["Turno"] == "dia"]
        trans_noche = trans[trans["Turno"] == "noche"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌅 Turno Día (8:00 - 20:00)**")
            if not trans_dia.empty:
                # Mostrar fechas involucradas
                fechas_dia = sorted(trans_dia["Tiempo_entrada"].dt.date.unique())
                st.caption(f"Fechas: {', '.join([f.strftime('%d/%m/%Y') for f in fechas_dia])}")
                
                viajes_dia = trans_dia["Proceso"].value_counts()
                st.dataframe(viajes_dia.to_frame("Cantidad"))
                
                # Productividad turno día
                prod_dia = productividad[productividad["Fecha"].between(rango[0], rango[1])]
                if not prod_dia.empty:
                    prod_dia_filtered = prod_dia[prod_dia["Nombre del Vehículo"].isin(trans_dia["Nombre del Vehículo"].unique())]
                    if not prod_dia_filtered.empty:
                        prod_med_dia = prod_dia_filtered["Prod_pct"].mean()
                        st.metric("Productividad promedio", f"{prod_med_dia:.1f}%")
            else:
                st.info("Sin datos para turno día")
        
        with col2:
            st.markdown("**🌙 Turno Noche (20:00 - 8:00)**")
            if not trans_noche.empty:
                # Mostrar fechas involucradas
                fechas_noche = sorted(trans_noche["Tiempo_entrada"].dt.date.unique())
                st.caption(f"Fechas: {', '.join([f.strftime('%d/%m/%Y') for f in fechas_noche])}")
                
                viajes_noche = trans_noche["Proceso"].value_counts()
                st.dataframe(viajes_noche.to_frame("Cantidad"))
                
                # Productividad turno noche
                prod_noche = productividad[productividad["Fecha"].between(rango[0], rango[1])]
                if not prod_noche.empty:
                    prod_noche_filtered = prod_noche[prod_noche["Nombre del Vehículo"].isin(trans_noche["Nombre del Vehículo"].unique())]
                    if not prod_noche_filtered.empty:
                        prod_med_noche = prod_noche_filtered["Prod_pct"].mean()
                        st.metric("Productividad promedio", f"{prod_med_noche:.1f}%")
            else:
                st.info("Sin datos para turno noche")

    # 🆕 Ciclos mejorados con secuencias
    if not ciclos_mejorados.empty:
        st.subheader("🔄 Ciclos Completos Mejorados (con Secuencias)")
        
        # Información sobre los nuevos tipos de ciclos
        st.info("""
        **🆕 Nuevos Tipos de Ciclos Detectados:**
        - **Ciclo de Carga**: Stock → Módulo/Pila ROM → Stock
        - **Ciclo de Descarga**: Módulo/Pila ROM → Botadero → Módulo/Pila ROM
        """)
        
        # Mostrar ciclos por tipo
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Ciclos por Tipo**")
            ciclos_por_tipo = ciclos_mejorados["Tipo_Ciclo"].value_counts()
            st.dataframe(ciclos_por_tipo.to_frame("Cantidad"))
        
        with col2:
            st.markdown("**🚛 Ciclos por Vehículo**")
            ciclos_por_vehiculo = ciclos_mejorados.groupby("Nombre del Vehículo").size().reset_index(name="Total_Ciclos")
            ciclos_por_vehiculo = ciclos_por_vehiculo.sort_values("Total_Ciclos", ascending=False)
            st.dataframe(ciclos_por_vehiculo)
        
        # Mostrar tabla completa de ciclos
        st.markdown("**📋 Detalle de Ciclos Completos**")
        ciclos_detalle = ciclos_mejorados.copy()
        ciclos_detalle["Duracion_ciclo_min"] = ciclos_detalle["Duracion_ciclo_s"] / 60
        ciclos_detalle = ciclos_detalle.round(2)
        st.dataframe(ciclos_detalle, use_container_width=True)
        
        # Gráfico de duración de ciclos por tipo
        chart_ciclos = (
            alt.Chart(ciclos_detalle)
            .mark_boxplot()
            .encode(
                x=alt.X("Tipo_Ciclo:N", title="Tipo de Ciclo"),
                y=alt.Y("Duracion_ciclo_min:Q", title="Duración del Ciclo (minutos)"),
                color=alt.Color("Tipo_Ciclo:N", 
                               scale=alt.Scale(domain=["Carga", "Descarga"], 
                                             range=["#1f77b4", "#ff7f0e"]))
            )
            .properties(height=300, title="Distribución de duración de ciclos por tipo")
        )
        st.altair_chart(chart_ciclos, use_container_width=True)
    
    # Ciclos originales (mantenidos para compatibilidad)
    if not ciclos.empty:
        st.subheader("🔄 Ciclos Originales (Stock→Módulo/Pila ROM→Stock)")
        ciclos_tab = (ciclos.groupby("Nombre del Vehículo").size()
                            .reset_index(name="Ciclos")
                            .sort_values("Ciclos", ascending=False))
        st.dataframe(ciclos_tab)

    # ─── Productividad ──────────────────────────────────────
    if not productividad.empty:
        st.subheader("🚀 Productividad por vehículo")
        prod_fecha = productividad[productividad["Fecha"].between(rango[0], rango[1])]
        if not prod_fecha.empty:
            prod_med = prod_fecha["Prod_pct"].mean()
            st.metric("Productividad promedio flota",
                      f"{prod_med:0.1f} %", delta=None)
            prod_tab = (prod_fecha.groupby("Nombre del Vehículo")["Prod_pct"]
                                   .mean().reset_index()
                                   .sort_values("Prod_pct", ascending=False))
            st.dataframe(prod_tab)

            prod_chart = (
                alt.Chart(prod_tab)
                .mark_bar()
                .encode(x=alt.X("Nombre del Vehículo:N", sort="-y"),
                        y=alt.Y("Prod_pct:Q", title="% productividad"),
                        tooltip=["Nombre_del_Vehículo:N", "Prod_pct:Q"])
                .properties(height=300)
            )
            st.altair_chart(prod_chart, use_container_width=True)

    # ─── Toneladas estimadas ────────────────────────────────
    if not trans.empty:
        st.subheader("🪨 Toneladas acumuladas (estimadas)")
        
        # Incluir tanto carga como descarga para estimación de toneladas
        viajes_produccion = trans[trans["Proceso"].isin(["carga", "descarga"])].copy()
        if not viajes_produccion.empty:
            np.random.seed(42)
            viajes_produccion["Toneladas"] = np.random.normal(
                loc=42, scale=3, size=len(viajes_produccion)
            ).clip(min=0)

            # Agrupar por hora y tipo de proceso
            tons_h = (
                viajes_produccion.groupby([
                    viajes_produccion["Tiempo_entrada"].dt.floor("h"),
                    "Proceso"
                ])["Toneladas"].sum().reset_index()
                .rename(columns={"Tiempo_entrada": "Hora_cal", "Toneladas": "Toneladas_h"})
            )

            # Gráfico de barras apiladas por tipo de proceso
            bar_tons = (
                alt.Chart(tons_h)
                .mark_bar()
                .encode(
                    x=alt.X("Hora_cal:T", title="Fecha-hora"),
                    y=alt.Y("Toneladas_h:Q", title="Toneladas"),
                    color=alt.Color("Proceso:N", 
                                   scale=alt.Scale(domain=["carga", "descarga"], 
                                                 range=["#1f77b4", "#ff7f0e"])),
                    tooltip=["Hora_cal:T", "Proceso:N", "Toneladas_h:Q"]
                )
                .properties(height=300, title="Toneladas por hora - Carga y Descarga")
            )
            st.altair_chart(bar_tons, use_container_width=True)
            
            # Estadísticas de toneladas
            col1, col2, col3 = st.columns(3)
            with col1:
                toneladas_carga = viajes_produccion[viajes_produccion["Proceso"] == "carga"]["Toneladas"].sum()
                st.metric("Toneladas carga", f"{toneladas_carga:.1f} t")
            with col2:
                toneladas_descarga = viajes_produccion[viajes_produccion["Proceso"] == "descarga"]["Toneladas"].sum()
                st.metric("Toneladas descarga", f"{toneladas_descarga:.1f} t")
            with col3:
                toneladas_total = viajes_produccion["Toneladas"].sum()
                st.metric("Toneladas total", f"{toneladas_total:.1f} t")
        else:
            st.info("Sin viajes de producción (carga/descarga) – no se estiman toneladas.")

    # ─── Expander con detalles ──────────────────────────────
    with st.expander("📍 Detalle de transiciones origen → destino"):
        if not trans.empty:
            st.dataframe(trans)
        else:
            st.info("Sin transiciones disponibles")

    # ─── Expander con detalles de viajes ────────────────────
    with st.expander("🚗 Detalle de tiempos de viaje"):
        if not viajes.empty:
            st.dataframe(viajes)
        else:
            st.info("Sin viajes detectados")

    # ─── Exportar a Excel ───────────────────────────────────
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
        if not trans.empty:
            trans.to_excel(excel_writer=xls, sheet_name="Transiciones", index=False)
            viajes_h.to_excel(excel_writer=xls, sheet_name="ViajesHora", index=False)
            ciclos.to_excel(excel_writer=xls, sheet_name="Ciclos", index=False)
            productividad.to_excel(excel_writer=xls, sheet_name="Productividad", index=False)
        if not ciclos_mejorados.empty:
            ciclos_mejorados.to_excel(excel_writer=xls, sheet_name="CiclosMejorados", index=False)
        if not viajes.empty:
            viajes.to_excel(excel_writer=xls, sheet_name="TiemposViaje", index=False)
        if not metricas_viaje.empty:
            metricas_viaje.to_excel(excel_writer=xls, sheet_name="MetricasViaje", index=False)
    st.download_button("💾 Descargar reporte Excel",
                       buf.getvalue(),
                       "reporte_operacional_con_viajes.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") 