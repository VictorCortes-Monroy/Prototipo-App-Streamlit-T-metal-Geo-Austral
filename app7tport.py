"""
Streamlit - T-Metal · Análisis de Secuencias de Viajes entre Geocercas Específicas
Versión 2025-01-31 – Dashboard simplificado para:
• Visualización de secuencias de viajes entre geocercas específicas
• Análisis de patrones de movimiento entre instalaciones
• Eliminación de métricas operacionales complejas
• Enfoque en secuencias origen-destino
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import unicodedata
from datetime import time
from io import BytesIO
import folium
from streamlit_folium import st_folium
from sklearn.cluster import DBSCAN
import re

st.set_page_config(
    page_title="🚛 T-Metal – Análisis de Secuencias de Viajes",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# Parámetros globales
# ─────────────────────────────────────────────────────────────
MIN_ESTANCIA_S      = 3  # Ajustado para datos de prueba (era 60)
SHIFT_DAY_START     = time(8, 0)
SHIFT_NIGHT_START   = time(20, 0)

# Geocercas específicas para análisis
GEOCERCAS_ESPECIFICAS: set[str] = set()
GEOCERCAS_EXCLUIDAS: set[str] = set()

# ─────────────────────────────────────────────────────────────
# Funciones copiadas de app6
# ─────────────────────────────────────────────────────────────
def turno(ts: pd.Timestamp) -> str:
    """
    Determina el turno basado en la hora.
    - Día: 08:00 - 19:59
    - Noche: 20:00 - 07:59 (del día siguiente)
    """
    h = ts.time()
    return "dia" if SHIFT_DAY_START <= h < SHIFT_NIGHT_START else "noche"

def turno_con_fecha(ts: pd.Timestamp) -> tuple[str, pd.Timestamp]:
    """
    Determina el turno y la fecha correspondiente.
    Para turnos de noche (20:00-07:59), la fecha es del día que inició el turno.
    
    Returns:
        tuple: (turno, fecha_turno)
    """
    h = ts.time()
    if SHIFT_DAY_START <= h < SHIFT_NIGHT_START:
        # Turno día: mismo día
        return "dia", ts.normalize()
    else:
        # Turno noche: si es antes de las 8:00, pertenece al turno del día anterior
        if h < SHIFT_DAY_START:
            # Es madrugada (00:00-07:59), pertenece al turno de noche del día anterior
            fecha_turno = ts.normalize() - pd.Timedelta(days=1)
        else:
            # Es noche (20:00-23:59), pertenece al turno de noche del mismo día
            fecha_turno = ts.normalize()
        return "noche", fecha_turno

def obtener_descripcion_turno(turno_tipo: str, fecha_turno: pd.Timestamp) -> str:
    """
    Genera descripción detallada del turno.
    """
    fecha_str = fecha_turno.strftime("%d-%m-%Y")
    if turno_tipo == "dia":
        return f"Turno Día {fecha_str} (08:00-19:59)"
    else:
        fecha_siguiente = (fecha_turno + pd.Timedelta(days=1)).strftime("%d-%m-%Y")
        return f"Turno Noche {fecha_str} (20:00 del {fecha_str} - 07:59 del {fecha_siguiente})"

def normalizar(s: str) -> str:
    """Quita tildes y pasa a minúsculas para detección robusta."""
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode("ascii")

def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y prepara el DataFrame de entrada."""
    df = df.copy()
    df["Tiempo de evento"] = pd.to_datetime(df["Tiempo de evento"])
    df["Geocercas"] = df["Geocercas"].fillna("").astype(str)
    df["Nombre del Vehículo"] = df["Nombre del Vehículo"].astype(str)
    return df.sort_values(["Nombre del Vehículo", "Tiempo de evento"])

def poblar_dominios(df: pd.DataFrame) -> None:
    """Define las geocercas específicas para el análisis de secuencias de viajes."""
    global GEOCERCAS_ESPECIFICAS, GEOCERCAS_EXCLUIDAS
    
    # Geocercas específicas para análisis de secuencias
    GEOCERCAS_ESPECIFICAS = {
        "Ciudad Mejillones",
        "Oxiquim", 
        "Puerto Mejillones",
        "Terquim",
        "Interacid",
        "Puerto Angamos",
        "TGN",
        "GNLM",
        "Muelle Centinela"
    }
    
    # Geocercas que deben ser excluidas del análisis (rutas, etc.)
    GEOCERCAS_EXCLUIDAS = {
        "Ruta - Afta Mejillones"
    }
    
    # Normalizar nombres para detección robusta
    geos_detectadas = set(df["Geocercas"].unique()) - {""}
    geos_normalizadas = {normalizar(geo) for geo in geos_detectadas}
    
    # Mapear geocercas detectadas a las específicas
    geocercas_encontradas = set()
    geocercas_excluidas_encontradas = set()
    
    for geo in geos_detectadas:
        geo_norm = normalizar(geo)
        
        # Verificar si es una geocerca excluida
        for geocerca_excluida in GEOCERCAS_EXCLUIDAS:
            if normalizar(geocerca_excluida) in geo_norm or geo_norm in normalizar(geocerca_excluida):
                geocercas_excluidas_encontradas.add(geocerca_excluida)
                break
        else:
            # Si no es excluida, verificar si es específica
            for geocerca_esp in GEOCERCAS_ESPECIFICAS:
                if normalizar(geocerca_esp) in geo_norm or geo_norm in normalizar(geocerca_esp):
                    geocercas_encontradas.add(geocerca_esp)
                    break
    
    globals()["GEOCERCAS_ENCONTRADAS"] = geocercas_encontradas
    globals()["GEOCERCAS_NO_ENCONTRADAS"] = GEOCERCAS_ESPECIFICAS - geocercas_encontradas
    globals()["GEOCERCAS_EXCLUIDAS_ENCONTRADAS"] = geocercas_excluidas_encontradas

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

    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g.copy().sort_values("Tiempo de evento")
        
        # 🔍 PASO 1: Detectar permanencias reales (filtrar ruido GPS)
        geocercas_validas = []
        tiempos_entrada = []
        tiempos_salida = []
        
        geocerca_actual = None
        tiempo_entrada_actual = None
        
        for i, row in g.iterrows():
            geo = str(row["Geocercas"]).strip()
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
        
        # 🔍 PASO 2: Crear transiciones entre permanencias válidas
        for i in range(len(geocercas_validas) - 1):
            origen = geocercas_validas[i]
            destino = geocercas_validas[i + 1]
            tiempo_salida_origen = tiempos_salida[i]
            tiempo_entrada_destino = tiempos_entrada[i + 1]
            
            # Duración de permanencia en el origen
            duracion_permanencia = (tiempo_salida_origen - tiempos_entrada[i]).total_seconds()
            
            total_cambios += 1
            
            turno_tipo, fecha_turno = turno_con_fecha(tiempos_entrada[i])
            transiciones_completas.append({
                "Nombre del Vehículo": veh,
                "Origen": origen,
                "Destino": destino,
                "Tiempo_entrada": tiempos_entrada[i],
                "Tiempo_salida": tiempo_salida_origen,
                "Duracion_s": duracion_permanencia,
                "Turno": turno_tipo,
                "Fecha_Turno": fecha_turno,
                "Descripcion_Turno": obtener_descripcion_turno(turno_tipo, fecha_turno)
            })

    if transiciones_completas:
        return pd.DataFrame(transiciones_completas)
    else:
        return pd.DataFrame(columns=[
            "Nombre del Vehículo", "Origen", "Destino",
            "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno", "Fecha_Turno", "Descripcion_Turno"
        ])

def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica secuencias de viajes entre geocercas específicas:
    - viaje_especifico: Ambos origen y destino están en geocercas específicas
    - viaje_parcial: Solo uno de origen o destino está en geocercas específicas
    - estadia_interna: Origen y destino son la misma geocerca (auto-transición)
    - otro: Movimientos que no involucran geocercas específicas o involucran geocercas excluidas
    """
    if df.empty:
        return df

    df = df.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    df["Proceso"] = "otro"  # Inicializar todos como "otro"

    # Obtener geocercas específicas y excluidas del contexto global
    GEOCERCAS_ESPECIFICAS = globals().get("GEOCERCAS_ESPECIFICAS", set())
    GEOCERCAS_EXCLUIDAS = globals().get("GEOCERCAS_EXCLUIDAS", set())

    # Procesar cada vehículo por separado
    grupos_procesados = []

    for veh, grupo in df.groupby("Nombre del Vehículo"):
        grupo = grupo.copy().sort_values("Tiempo_entrada").reset_index(drop=True)

        for i in range(len(grupo)):
            origen = grupo.loc[i, "Origen"]
            destino = grupo.loc[i, "Destino"]

            # Si origen y destino son la misma geocerca, es una estadía interna
            if origen == destino:
                grupo.loc[i, "Proceso"] = "estadia_interna"
                continue

            # Verificar si origen o destino están en geocercas excluidas
            origen_excluido = any(geocerca_excluida in origen for geocerca_excluida in GEOCERCAS_EXCLUIDAS)
            destino_excluido = any(geocerca_excluida in destino for geocerca_excluida in GEOCERCAS_EXCLUIDAS)
            
            # Si alguno está excluido, marcar como "otro"
            if origen_excluido or destino_excluido:
                grupo.loc[i, "Proceso"] = "otro"
                continue

            # Verificar si ambos origen y destino están en geocercas específicas
            origen_especifico = any(geocerca_esp in origen for geocerca_esp in GEOCERCAS_ESPECIFICAS)
            destino_especifico = any(geocerca_esp in destino for geocerca_esp in GEOCERCAS_ESPECIFICAS)
            
            if origen_especifico and destino_especifico:
                grupo.loc[i, "Proceso"] = "viaje_especifico"
            elif origen_especifico or destino_especifico:
                grupo.loc[i, "Proceso"] = "viaje_parcial"
            else:
                grupo.loc[i, "Proceso"] = "otro"

        grupos_procesados.append(grupo)

    if grupos_procesados:
        return pd.concat(grupos_procesados, ignore_index=True)
    else:
        return df

def consolidar_estadias_internas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida las estadías internas (auto-transiciones) con el viaje válido anterior.
    Por ejemplo: si hay un viaje "Ciudad Mejillones -> TGN" seguido de varias "TGN -> TGN",
    se consolida todo como una estadía extendida en TGN.
    """
    if df.empty:
        return df

    df = df.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    grupos_consolidados = []

    for veh, grupo in df.groupby("Nombre del Vehículo"):
        grupo = grupo.copy().sort_values("Tiempo_entrada").reset_index(drop=True)
        registros_finales = []
        
        i = 0
        while i < len(grupo):
            registro_actual = grupo.iloc[i].copy()
            
            # Si es una estadía interna, buscar el viaje válido anterior
            if registro_actual["Proceso"] == "estadia_interna":
                # Buscar el último viaje válido anterior (viaje_especifico o viaje_parcial)
                viaje_anterior_idx = None
                for j in range(i - 1, -1, -1):
                    if grupo.iloc[j]["Proceso"] in ["viaje_especifico", "viaje_parcial"]:
                        viaje_anterior_idx = j
                        break
                
                if viaje_anterior_idx is not None:
                    # Extender el viaje anterior con esta estadía interna
                    registros_finales[viaje_anterior_idx]["Tiempo_salida"] = registro_actual["Tiempo_salida"]
                    registros_finales[viaje_anterior_idx]["Duracion_s"] = (
                        registros_finales[viaje_anterior_idx]["Tiempo_salida"] - 
                        registros_finales[viaje_anterior_idx]["Tiempo_entrada"]
                    ).total_seconds()
                    
                    # Agregar información sobre la estadía interna consolidada
                    if "Estadias_Consolidadas" not in registros_finales[viaje_anterior_idx]:
                        registros_finales[viaje_anterior_idx]["Estadias_Consolidadas"] = 0
                    registros_finales[viaje_anterior_idx]["Estadias_Consolidadas"] += 1
                    
                    # Buscar más estadías internas consecutivas
                    k = i + 1
                    while k < len(grupo) and grupo.iloc[k]["Proceso"] == "estadia_interna":
                        estadia_adicional = grupo.iloc[k]
                        registros_finales[viaje_anterior_idx]["Tiempo_salida"] = estadia_adicional["Tiempo_salida"]
                        registros_finales[viaje_anterior_idx]["Duracion_s"] = (
                            registros_finales[viaje_anterior_idx]["Tiempo_salida"] - 
                            registros_finales[viaje_anterior_idx]["Tiempo_entrada"]
                        ).total_seconds()
                        registros_finales[viaje_anterior_idx]["Estadias_Consolidadas"] += 1
                        k += 1
                    
                    i = k  # Saltar todas las estadías internas procesadas
                else:
                    # No hay viaje válido anterior, mantener como estadía interna
                    registros_finales.append(registro_actual)
                    i += 1
            else:
                # No es estadía interna, agregar normalmente
                registros_finales.append(registro_actual)
                i += 1
        
        if registros_finales:
            grupo_consolidado = pd.DataFrame(registros_finales)
            grupos_consolidados.append(grupo_consolidado)

    if grupos_consolidados:
        return pd.concat(grupos_consolidados, ignore_index=True)
    else:
        return df

def extraer_tiempos_viaje(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae tiempos de viaje cuando la geocerca está vacía."""
    viajes = []
    casos_desconocidos = {"origen": 0, "destino": 0, "ambos": 0}
    
    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g.copy().sort_values("Tiempo de evento").reset_index(drop=True)
        
        # Identificar grupos de registros consecutivos en viaje (geocerca vacía)
        g["es_viaje"] = g["Geocercas"] == ""
        g["grupo_viaje"] = (g["es_viaje"] != g["es_viaje"].shift()).cumsum()
        
        # Procesar solo grupos que son viajes
        grupos_viaje = g[g["es_viaje"]].groupby("grupo_viaje")
        
        for grupo_id, grupo in grupos_viaje:
            if len(grupo) < 2:  # Necesitamos al menos 2 registros para calcular duración
                continue
                
            inicio = grupo["Tiempo de evento"].iloc[0]
            fin = grupo["Tiempo de evento"].iloc[-1]
            duracion_s = (fin - inicio).total_seconds()
            
            if duracion_s < 30:  # Filtrar viajes muy cortos
                continue
            
            # Encontrar origen y destino con búsqueda mejorada
            idx_inicio_grupo = grupo.index[0]
            idx_fin_grupo = grupo.index[-1]
            
            # Buscar geocerca anterior (origen) - búsqueda más amplia
            origen = "DESCONOCIDO"
            # Buscar hacia atrás en todo el DataFrame del vehículo
            registros_anteriores = g[g.index < idx_inicio_grupo]
            if not registros_anteriores.empty:
                # Buscar el último registro con geocerca no vacía
                geocercas_anteriores = registros_anteriores[registros_anteriores["Geocercas"] != ""]
                if not geocercas_anteriores.empty:
                    origen = geocercas_anteriores["Geocercas"].iloc[-1]
            
            # Buscar geocerca posterior (destino) - búsqueda más amplia  
            destino = "DESCONOCIDO"
            # Buscar hacia adelante en todo el DataFrame del vehículo
            registros_posteriores = g[g.index > idx_fin_grupo]
            if not registros_posteriores.empty:
                # Buscar el primer registro con geocerca no vacía
                geocercas_posteriores = registros_posteriores[registros_posteriores["Geocercas"] != ""]
                if not geocercas_posteriores.empty:
                    destino = geocercas_posteriores["Geocercas"].iloc[0]
            
            # Contar casos desconocidos para diagnóstico
            if origen == "DESCONOCIDO" and destino == "DESCONOCIDO":
                casos_desconocidos["ambos"] += 1
            elif origen == "DESCONOCIDO":
                casos_desconocidos["origen"] += 1
            elif destino == "DESCONOCIDO":
                casos_desconocidos["destino"] += 1
            
            turno_tipo, fecha_turno = turno_con_fecha(inicio)
            viajes.append({
                "Nombre del Vehículo": veh,
                "Origen": origen,
                "Destino": destino,
                "Inicio_viaje": inicio,
                "Fin_viaje": fin,
                "Duracion_viaje_s": duracion_s,
                "Turno": turno_tipo,
                "Fecha_Turno": fecha_turno,
                "Descripcion_Turno": obtener_descripcion_turno(turno_tipo, fecha_turno)
            })
    
    # Logging para diagnóstico
    if casos_desconocidos["origen"] > 0 or casos_desconocidos["destino"] > 0 or casos_desconocidos["ambos"] > 0:
        print(f"🔍 Diagnóstico de casos DESCONOCIDO:")
        print(f"   - Solo origen desconocido: {casos_desconocidos['origen']} viajes")
        print(f"   - Solo destino desconocido: {casos_desconocidos['destino']} viajes")
        print(f"   - Ambos desconocidos: {casos_desconocidos['ambos']} viajes")
        print(f"   - Total viajes válidos: {len(viajes)}")
    
    if viajes:
        return pd.DataFrame(viajes)
    else:
        return pd.DataFrame(columns=[
            "Nombre del Vehículo", "Origen", "Destino",
            "Inicio_viaje", "Fin_viaje", "Duracion_viaje_s", "Turno", "Fecha_Turno", "Descripcion_Turno"
        ])

def construir_analisis_horario(trans_filtradas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Construye análisis detallado de viajes por hora.
    
    Returns:
        tuple: (viajes_por_hora_general, viajes_por_hora_por_vehiculo)
    """
    if trans_filtradas.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Filtrar solo viajes válidos (específicos y parciales)
    viajes_validos = trans_filtradas[trans_filtradas["Proceso"].isin(["viaje_especifico", "viaje_parcial"])].copy()
    
    if viajes_validos.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Crear columnas de hora, fecha y descripción de turno
    viajes_produccion["Hora"] = viajes_produccion["Tiempo_entrada"].dt.hour
    viajes_produccion["Fecha"] = viajes_produccion["Tiempo_entrada"].dt.date
    viajes_produccion["Hora_str"] = viajes_produccion["Tiempo_entrada"].dt.strftime("%H:00")
    viajes_produccion["Fecha_Hora"] = viajes_produccion["Tiempo_entrada"].dt.strftime("%Y-%m-%d %H:00")
    
    # ─── ANÁLISIS GENERAL POR HORA ───
    analisis_general = viajes_produccion.groupby(["Fecha_Hora", "Hora_str", "Proceso"]).agg({
        "Nombre del Vehículo": "count",
        "Descripcion_Turno": "first"
    }).rename(columns={"Nombre del Vehículo": "Cantidad_Viajes"}).reset_index()
    
    # Ordenar por fecha-hora
    analisis_general = analisis_general.sort_values("Fecha_Hora")
    
    # ─── ANÁLISIS POR VEHÍCULO Y HORA ───
    analisis_por_vehiculo = viajes_produccion.groupby([
        "Nombre del Vehículo", "Fecha_Hora", "Hora_str", "Proceso"
    ]).agg({
        "Tiempo_entrada": "count",
        "Descripcion_Turno": "first",
        "Origen": lambda x: ", ".join(x.unique()),
        "Destino": lambda x: ", ".join(x.unique())
    }).rename(columns={
        "Tiempo_entrada": "Cantidad_Viajes"
    }).reset_index()
    
    # Ordenar por vehículo y fecha-hora
    analisis_por_vehiculo = analisis_por_vehiculo.sort_values(["Nombre del Vehículo", "Fecha_Hora"])
    
    return analisis_general, analisis_por_vehiculo

def construir_metricas_viaje(viajes: pd.DataFrame) -> pd.DataFrame:
    """Construye métricas detalladas por vehículo para tiempos de viaje."""
    if viajes.empty:
        return pd.DataFrame()
    
    metricas_vehiculo = viajes.groupby("Nombre del Vehículo").agg({
        "Duracion_viaje_s": ["count", "mean", "std", "min", "max"]
    }).round(2)
    
    # Flatten column names
    metricas_vehiculo.columns = [f"{col[0]}_{col[1]}" for col in metricas_vehiculo.columns]
    metricas_vehiculo = metricas_vehiculo.reset_index()
    
    # Convertir a minutos para mejor legibilidad
    for col in ["Duracion_viaje_s_mean", "Duracion_viaje_s_min", "Duracion_viaje_s_max"]:
        metricas_vehiculo[col.replace("_s", "_min")] = (metricas_vehiculo[col] / 60).round(1)
    
    # Renombrar columnas con nombres más claros y entendibles
    metricas_vehiculo = metricas_vehiculo.rename(columns={
        "Nombre del Vehículo": "Vehículo",
        "Duracion_viaje_s_count": "Total de Viajes",
        "Duracion_viaje_s_mean": "Tiempo Promedio (seg)",
        "Duracion_viaje_s_std": "Desviación Estándar (seg)",
        "Duracion_viaje_s_min": "Tiempo Mínimo (seg)",
        "Duracion_viaje_s_max": "Tiempo Máximo (seg)",
        "Duracion_viaje_min_mean": "Tiempo Promedio (min)",
        "Duracion_viaje_min_min": "Tiempo Mínimo (min)",
        "Duracion_viaje_min_max": "Tiempo Máximo (min)"
    })
    
    # Seleccionar solo las columnas más relevantes y en orden lógico
    columnas_finales = [
        "Vehículo",
        "Total de Viajes", 
        "Tiempo Promedio (min)",
        "Tiempo Mínimo (min)",
        "Tiempo Máximo (min)",
        "Desviación Estándar (seg)"
    ]
    
    # Filtrar solo las columnas que existen
    columnas_existentes = [col for col in columnas_finales if col in metricas_vehiculo.columns]
    metricas_vehiculo = metricas_vehiculo[columnas_existentes]
    
    return metricas_vehiculo

def extraer_coordenadas_url(url_mapa: str) -> tuple:
    """Extrae coordenadas de la URL del mapa de Google."""
    if pd.isna(url_mapa) or url_mapa == "":
        return None, None
    
    # Buscar patrón de coordenadas en la URL
    patron = r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)'
    match = re.search(patron, str(url_mapa))
    
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon
    
    return None, None

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos GPS usando la fórmula de Haversine."""
    R = 6371000  # Radio de la Tierra en metros
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)
    
    a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def agrupar_zonas_cercanas(zonas_df: pd.DataFrame, radio_metros: float = 10.0) -> pd.DataFrame:
    """
    Agrupa zonas candidatas que están dentro de un radio específico usando clustering.
    """
    if zonas_df.empty:
        return zonas_df
    
    # Preparar coordenadas para clustering
    coordenadas = zonas_df[["Latitud_Centro", "Longitud_Centro"]].values
    
    # Convertir radio de metros a grados aproximadamente
    # 1 grado ≈ 111,000 metros
    radio_grados = radio_metros / 111000
    
    # Usar DBSCAN para clustering basado en distancia
    clustering = DBSCAN(eps=radio_grados, min_samples=1, metric='haversine')
    clusters = clustering.fit_predict(np.radians(coordenadas))
    
    # Agrupar zonas por cluster
    zonas_agrupadas = []
    
    for cluster_id in np.unique(clusters):
        if cluster_id == -1:  # Ruido (no debería ocurrir con min_samples=1)
            continue
            
        zonas_cluster = zonas_df[clusters == cluster_id]
        
        if len(zonas_cluster) == 1:
            # Solo una zona en el cluster, mantener original
            zona = zonas_cluster.iloc[0].to_dict()
            zona["Zonas_Agrupadas"] = 1
            zona["Vehiculos_Involucrados"] = [zona["Nombre del Vehículo"]]
            zonas_agrupadas.append(zona)
        else:
            # Múltiples zonas, crear zona agrupada
            # Calcular centro ponderado por duración
            pesos = zonas_cluster["Duracion_Minutos"].values
            lat_centro = np.average(zonas_cluster["Latitud_Centro"], weights=pesos)
            lon_centro = np.average(zonas_cluster["Longitud_Centro"], weights=pesos)
            
            # Calcular radio máximo del cluster
            distancias = []
            for _, zona in zonas_cluster.iterrows():
                dist = calcular_distancia_haversine(lat_centro, lon_centro, 
                                                  zona["Latitud_Centro"], zona["Longitud_Centro"])
                distancias.append(dist)
            radio_cluster = max(distancias) if distancias else 0
            
            zona_agrupada = {
                "Nombre del Vehículo": f"AGRUPADA ({len(zonas_cluster)} zonas)",
                "Latitud_Centro": lat_centro,
                "Longitud_Centro": lon_centro,
                "Duracion_Minutos": zonas_cluster["Duracion_Minutos"].sum(),
                "Registros": zonas_cluster["Registros"].sum(),
                "Radio_Aprox_m": max(radio_cluster, zonas_cluster["Radio_Aprox_m"].max()),
                "Inicio": zonas_cluster["Inicio"].min(),
                "Fin": zonas_cluster["Fin"].max(),
                "Velocidad_Promedio": zonas_cluster["Velocidad_Promedio"].mean(),
                "Zonas_Agrupadas": len(zonas_cluster),
                "Vehiculos_Involucrados": zonas_cluster["Nombre del Vehículo"].tolist()
            }
            zonas_agrupadas.append(zona_agrupada)
    
    if zonas_agrupadas:
        resultado = pd.DataFrame(zonas_agrupadas)
        # Ordenar por duración descendente
        resultado = resultado.sort_values("Duracion_Minutos", ascending=False).reset_index(drop=True)
        return resultado
    else:
        return pd.DataFrame()

def analizar_zonas_no_mapeadas(df: pd.DataFrame, velocidad_max: float = 5.0, tiempo_min_minutos: int = 10, radio_agrupacion: float = 10.0) -> pd.DataFrame:
    """
    Identifica zonas donde los vehículos permanecen mucho tiempo fuera de geocercas
    con baja velocidad, sugiriendo posibles geocercas no mapeadas.
    Incluye agrupación de zonas cercanas.
    """
    # Filtrar registros fuera de geocercas
    fuera_geocercas = df[df["Geocercas"] == ""].copy()
    
    if fuera_geocercas.empty:
        return pd.DataFrame()
    
    # Filtrar por velocidad baja (o NaN que indica parado)
    fuera_geocercas["Velocidad [km/h]"] = pd.to_numeric(fuera_geocercas["Velocidad [km/h]"], errors='coerce')
    baja_velocidad = fuera_geocercas[
        (fuera_geocercas["Velocidad [km/h]"].isna()) | 
        (fuera_geocercas["Velocidad [km/h]"] <= velocidad_max)
    ].copy()
    
    if baja_velocidad.empty:
        return pd.DataFrame()
    
    # Extraer coordenadas de latitud/longitud directamente
    baja_velocidad = baja_velocidad.dropna(subset=["Latitud", "Longitud"])
    
    if baja_velocidad.empty:
        return pd.DataFrame()
    
    # Convertir a numérico
    baja_velocidad["Latitud"] = pd.to_numeric(baja_velocidad["Latitud"], errors='coerce')
    baja_velocidad["Longitud"] = pd.to_numeric(baja_velocidad["Longitud"], errors='coerce')
    baja_velocidad = baja_velocidad.dropna(subset=["Latitud", "Longitud"])
    
    if len(baja_velocidad) < 10:  # Necesitamos suficientes puntos
        return pd.DataFrame()
    
    # Agrupar por vehículo y analizar permanencias
    zonas_candidatas = []
    
    for veh, grupo in baja_velocidad.groupby("Nombre del Vehículo"):
        grupo = grupo.sort_values("Tiempo de evento").reset_index(drop=True)
        
        # Identificar grupos temporales consecutivos (permanencias)
        grupo["tiempo_diff"] = grupo["Tiempo de evento"].diff().dt.total_seconds().fillna(0)
        grupo["nuevo_grupo"] = (grupo["tiempo_diff"] > 300).cumsum()  # 5 minutos de separación
        
        for grupo_id, subgrupo in grupo.groupby("nuevo_grupo"):
            if len(subgrupo) < 3:  # Mínimo 3 registros
                continue
                
            duracion_minutos = (subgrupo["Tiempo de evento"].max() - subgrupo["Tiempo de evento"].min()).total_seconds() / 60
            
            if duracion_minutos >= tiempo_min_minutos:
                # Calcular centro de la zona
                lat_centro = subgrupo["Latitud"].mean()
                lon_centro = subgrupo["Longitud"].mean()
                
                # Calcular dispersión (radio aproximado)
                lat_std = subgrupo["Latitud"].std()
                lon_std = subgrupo["Longitud"].std()
                radio_aprox = np.sqrt(lat_std**2 + lon_std**2) * 111000  # Conversión aproximada a metros
                
                zonas_candidatas.append({
                    "Nombre del Vehículo": veh,
                    "Latitud_Centro": lat_centro,
                    "Longitud_Centro": lon_centro,
                    "Duracion_Minutos": duracion_minutos,
                    "Registros": len(subgrupo),
                    "Radio_Aprox_m": radio_aprox,
                    "Inicio": subgrupo["Tiempo de evento"].min(),
                    "Fin": subgrupo["Tiempo de evento"].max(),
                    "Velocidad_Promedio": subgrupo["Velocidad [km/h]"].mean()
                })
    
    if not zonas_candidatas:
        return pd.DataFrame()
    
    # Crear DataFrame inicial
    zonas_df = pd.DataFrame(zonas_candidatas)
    
    # Agrupar zonas cercanas
    zonas_agrupadas = agrupar_zonas_cercanas(zonas_df, radio_agrupacion)
    
    return zonas_agrupadas

def crear_mapa_calor(df: pd.DataFrame, zonas_candidatas: pd.DataFrame) -> folium.Map:
    """Crea un mapa de calor con las zonas candidatas y geocercas existentes."""
    
    # Calcular centro del mapa
    if not df.empty and "Latitud" in df.columns and "Longitud" in df.columns:
        df_coords = df.dropna(subset=["Latitud", "Longitud"])
        if not df_coords.empty:
            centro_lat = df_coords["Latitud"].mean()
            centro_lon = df_coords["Longitud"].mean()
        else:
            centro_lat, centro_lon = -22.59, -69.86  # Coordenadas por defecto
    else:
        centro_lat, centro_lon = -22.59, -69.86
    
    # Crear mapa base
    mapa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Añadir geocercas conocidas
    geocercas_conocidas = df[df["Geocercas"] != ""].dropna(subset=["Latitud", "Longitud"])
    if not geocercas_conocidas.empty:
        for geocerca in geocercas_conocidas["Geocercas"].unique():
            puntos_geocerca = geocercas_conocidas[geocercas_conocidas["Geocercas"] == geocerca]
            if not puntos_geocerca.empty:
                lat_media = puntos_geocerca["Latitud"].mean()
                lon_media = puntos_geocerca["Longitud"].mean()
                
                folium.Marker(
                    [lat_media, lon_media],
                    popup=f"Geocerca: {geocerca}",
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(mapa)
    
    # Añadir zonas candidatas
    if not zonas_candidatas.empty:
        for idx, zona in zonas_candidatas.iterrows():
            # Determinar si es zona agrupada
            es_agrupada = zona.get("Zonas_Agrupadas", 1) > 1
            color = 'orange' if es_agrupada else 'red'
            
            # Preparar información del popup
            if es_agrupada:
                vehiculos_info = ", ".join(zona.get("Vehiculos_Involucrados", [zona["Nombre del Vehículo"]]))
                popup_text = f"""
                <b>Zona Agrupada</b><br>
                Zonas combinadas: {zona.get("Zonas_Agrupadas", 1)}<br>
                Vehículos: {vehiculos_info}<br>
                Duración Total: {zona["Duracion_Minutos"]:.1f} min<br>
                Registros: {zona["Registros"]}<br>
                Velocidad Prom: {zona["Velocidad_Promedio"]:.1f} km/h<br>
                Radio: {zona["Radio_Aprox_m"]:.0f} m
                """
            else:
                popup_text = f"""
                <b>Zona Individual</b><br>
                Vehículo: {zona["Nombre del Vehículo"]}<br>
                Duración: {zona["Duracion_Minutos"]:.1f} min<br>
                Registros: {zona["Registros"]}<br>
                Velocidad Prom: {zona["Velocidad_Promedio"]:.1f} km/h<br>
                Radio: {zona["Radio_Aprox_m"]:.0f} m
                """
            
            folium.CircleMarker(
                [zona["Latitud_Centro"], zona["Longitud_Centro"]],
                radius=min(max(zona["Duracion_Minutos"] / 10, 5), 25),  # Radio proporcional a duración
                popup=popup_text,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7 if es_agrupada else 0.6
            ).add_to(mapa)
    
    return mapa

# ─────────────────────────────────────────────────────────────
# Interfaz Streamlit Reorganizada
# ─────────────────────────────────────────────────────────────
st.header("📤 Carga de archivo CSV – Análisis de Secuencias de Viajes entre Geocercas Específicas")
archivo = st.file_uploader("Selecciona el CSV exportado desde GeoAustral", type=["csv"])

if archivo:
    raw = pd.read_csv(archivo)
    df = preparar_datos(raw)
    poblar_dominios(df)

    # ─── Procesamiento inicial ─────────────────────────────────
    trans_inicial = extraer_transiciones(df)
    viajes_inicial = extraer_tiempos_viaje(df)
    
    if trans_inicial.empty and viajes_inicial.empty:
        st.warning("No se encontraron transiciones válidas ni viajes detectados.")
        st.stop()

    # Clasificar procesos
    trans_inicial = clasificar_proceso_con_secuencia(trans_inicial)
    
    # Consolidar estadías internas (auto-transiciones)
    trans_inicial = consolidar_estadias_internas(trans_inicial)
    
    # ─── SECCIÓN 1: Geocercas Específicas ────────────────────────
    st.subheader("🏭 Geocercas Específicas para Análisis de Secuencias")
    
    GEOCERCAS_ESPECIFICAS = globals().get("GEOCERCAS_ESPECIFICAS", set())
    GEOCERCAS_ENCONTRADAS = globals().get("GEOCERCAS_ENCONTRADAS", set())
    GEOCERCAS_NO_ENCONTRADAS = globals().get("GEOCERCAS_NO_ENCONTRADAS", set())
    GEOCERCAS_EXCLUIDAS = globals().get("GEOCERCAS_EXCLUIDAS", set())
    GEOCERCAS_EXCLUIDAS_ENCONTRADAS = globals().get("GEOCERCAS_EXCLUIDAS_ENCONTRADAS", set())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**✅ Geocercas Encontradas en Datos:**")
        if GEOCERCAS_ENCONTRADAS:
            for geocerca in sorted(GEOCERCAS_ENCONTRADAS):
                st.write(f"• {geocerca}")
        else:
            st.write("Ninguna encontrada")
    
    with col2:
        st.markdown("**❌ Geocercas No Encontradas:**")
        if GEOCERCAS_NO_ENCONTRADAS:
            for geocerca in sorted(GEOCERCAS_NO_ENCONTRADAS):
                st.write(f"• {geocerca}")
        else:
            st.write("Todas las geocercas fueron encontradas")
    
    with col3:
        st.markdown("**🚫 Geocercas Excluidas (Rutas):**")
        if GEOCERCAS_EXCLUIDAS_ENCONTRADAS:
            for geocerca in sorted(GEOCERCAS_EXCLUIDAS_ENCONTRADAS):
                st.write(f"• {geocerca}")
        else:
            st.write("Ninguna encontrada")
    
    # Mostrar estadísticas de detección
    total_geocercas = len(GEOCERCAS_ESPECIFICAS)
    encontradas = len(GEOCERCAS_ENCONTRADAS)
    porcentaje = (encontradas / total_geocercas * 100) if total_geocercas > 0 else 0
    
    st.info(f"""
    **📊 Estadísticas de Detección:**
    - Total de geocercas específicas: {total_geocercas}
    - Geocercas encontradas: {encontradas}
    - Geocercas no encontradas: {len(GEOCERCAS_NO_ENCONTRADAS)}
    - Geocercas excluidas encontradas: {len(GEOCERCAS_EXCLUIDAS_ENCONTRADAS)}
    - Porcentaje de detección: {porcentaje:.1f}%
    """)
    
    if GEOCERCAS_NO_ENCONTRADAS:
        st.warning(f"""
        **⚠️ Geocercas no encontradas en los datos:**
        {', '.join(sorted(GEOCERCAS_NO_ENCONTRADAS))}
        
        Esto puede deberse a:
        - Diferencias en el nombre exacto de las geocercas
        - Geocercas que no están presentes en el período de datos
        - Errores de ortografía o formato en los nombres
        """)
    
    if GEOCERCAS_EXCLUIDAS_ENCONTRADAS:
        st.info(f"""
        **ℹ️ Geocercas excluidas del análisis (rutas):**
        {', '.join(sorted(GEOCERCAS_EXCLUIDAS_ENCONTRADAS))}
        
        Estas geocercas representan rutas y no se consideran como destinos válidos para el análisis de secuencias de viajes.
        """)

    # ─── SECCIÓN 2: Filtros ────────────────────────
    st.subheader("🔍 Filtros de Análisis")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Filtro de fecha
        dmin, dmax = df["Tiempo de evento"].dt.date.min(), df["Tiempo de evento"].dt.date.max()
        rango = st.date_input("Rango de fechas", [dmin, dmax])
        if isinstance(rango, tuple): rango = list(rango)
        if len(rango) == 1: rango = [rango[0], rango[0]]
    
    with col2:
        # Filtro de vehículo
        veh_opts = ["Todos"] + sorted(df["Nombre del Vehículo"].unique())
        veh_sel = st.selectbox("Vehículo", veh_opts)
    
    with col3:
        st.write("")  # Espacio vacío para mantener layout
    
    with col4:
        st.write("")  # Espacio vacío para mantener layout
    
    with col5:
        st.write("")  # Espacio vacío para mantener layout

    # ─── FILTRO ADICIONAL: Rango de Horas ────────────────────────
    st.markdown("**⏰ Filtro por Rango de Horas:**")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Crear DataFrame con fechas filtradas para obtener rango de horas
        df_temp = df[(df["Tiempo de evento"].dt.date >= rango[0]) & 
                     (df["Tiempo de evento"].dt.date <= rango[1])]
        
        if not df_temp.empty:
            hora_min = df_temp["Tiempo de evento"].dt.hour.min()
            hora_max = df_temp["Tiempo de evento"].dt.hour.max()
        else:
            hora_min, hora_max = 0, 23
        
        rango_horas = st.slider(
            "Seleccionar rango de horas",
            min_value=0, max_value=23,
            value=(hora_min, hora_max),
            help="Filtra los datos por rango de horas dentro de las fechas seleccionadas"
        )
    
    with col2:
        st.info(f"""
        **Rango seleccionado:** {rango_horas[0]:02d}:00 - {rango_horas[1]:02d}:59
        
        **Turnos incluidos:**
        • Día (08:00-19:59): {'✅' if (rango_horas[0] <= 19 and rango_horas[1] >= 8) else '❌'}
        • Noche (20:00-07:59): {'✅' if (rango_horas[0] <= 7 or rango_horas[1] >= 20) else '❌'}
        """)
    
    with col3:
        aplicar_filtro_horas = st.checkbox("Aplicar filtro de horas", value=False)

    # Aplicar filtros a los datos
    df_filtrado = df[(df["Tiempo de evento"].dt.date >= rango[0]) & 
                     (df["Tiempo de evento"].dt.date <= rango[1])]
    
    # Aplicar filtro de horas si está activado
    if aplicar_filtro_horas:
        hora_inicio, hora_fin = rango_horas
        df_filtrado = df_filtrado[
            (df_filtrado["Tiempo de evento"].dt.hour >= hora_inicio) &
            (df_filtrado["Tiempo de evento"].dt.hour <= hora_fin)
        ]
    
    if veh_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nombre del Vehículo"] == veh_sel]
    
    # Procesar datos filtrados
    trans = extraer_transiciones(df_filtrado)
    viajes = extraer_tiempos_viaje(df_filtrado)
    
    if not trans.empty:
        trans = clasificar_proceso_con_secuencia(trans)
        # Consolidar estadías internas (auto-transiciones)
        trans = consolidar_estadias_internas(trans)
    
    # Filtrar transiciones (sin filtros de origen/destino específicos)
    trans_filtradas = trans.copy()

    # ─── SECCIÓN 3: Matriz de Secuencias de Viajes ────────────────────────
    st.subheader("📊 Matriz de Secuencias de Viajes entre Geocercas Específicas")
    
    # Mostrar información sobre consolidación de estadías internas
    if not trans_filtradas.empty:
        viajes_con_consolidacion = trans_filtradas[trans_filtradas["Proceso"].isin(["viaje_especifico", "viaje_parcial"])]
        if "Estadias_Consolidadas" in viajes_con_consolidacion.columns:
            total_consolidaciones = viajes_con_consolidacion["Estadias_Consolidadas"].sum()
            viajes_con_consolidacion_count = len(viajes_con_consolidacion[viajes_con_consolidacion["Estadias_Consolidadas"] > 0])
            
            if total_consolidaciones > 0:
                st.info(f"""
                **🔄 Estadías Internas Consolidadas:**
                - Total de estadías internas consolidadas: {total_consolidaciones}
                - Viajes que incluyen estadías consolidadas: {viajes_con_consolidacion_count}
                - Promedio de estadías por viaje consolidado: {total_consolidaciones/viajes_con_consolidacion_count:.1f}
                
                *Las auto-transiciones (ej: TGN→TGN) se han consolidado con el viaje válido anterior, extendiendo la duración de la estadía en el destino.*
                """)
    
    if not trans_filtradas.empty:
        viajes_especificos = trans_filtradas[trans_filtradas["Proceso"].isin(["viaje_especifico", "viaje_parcial"])].copy()
        
        if not viajes_especificos.empty:
            # Preparar columnas adicionales para análisis temporal
            viajes_especificos["Fecha_str"] = viajes_especificos["Fecha_Turno"].dt.strftime("%d/%m/%Y")
            viajes_especificos["Turno_str"] = viajes_especificos["Turno"].map({"dia": "Día", "noche": "Noche"})
            
            # Tabs expandidas para mostrar diferentes matrices
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Matriz General", 
                "📅 Matriz por Fecha", 
                "🌅 Matriz por Turno",
                "📅🌅 Matriz Fecha-Turno",
                "🚛 Detalle por Vehículo"
            ])
            
            with tab1:
                st.markdown("**Matriz General de Viajes Origen → Destino**")
                
                # Crear matriz de origen-destino general
                matriz_viajes = viajes_especificos.groupby(["Origen", "Destino", "Proceso"]).size().reset_index(name="Cantidad")
                
                # Pivot para mostrar como matriz
                matriz_pivot = matriz_viajes.pivot_table(
                    index="Origen", 
                    columns="Destino", 
                    values="Cantidad", 
                    aggfunc="sum", 
                    fill_value=0
                )
                
                st.dataframe(matriz_pivot, use_container_width=True)
                
                # Estadísticas de la matriz general
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_especificos = len(viajes_especificos[viajes_especificos["Proceso"] == "viaje_especifico"])
                    st.metric("Viajes Específicos", total_especificos)
                with col2:
                    total_parciales = len(viajes_especificos[viajes_especificos["Proceso"] == "viaje_parcial"])
                    st.metric("Viajes Parciales", total_parciales)
                with col3:
                    total_viajes = total_especificos + total_parciales
                    st.metric("Total Viajes", total_viajes)
            
            with tab2:
                st.markdown("**📅 Matriz de Viajes por Fecha**")
                
                # Matriz agrupada por fecha
                matriz_por_fecha = viajes_especificos.groupby(["Fecha_str", "Proceso"]).size().reset_index(name="Cantidad")
                
                # Pivot por fecha
                matriz_fecha_pivot = matriz_por_fecha.pivot_table(
                    index="Fecha_str",
                    columns="Proceso",
                    values="Cantidad",
                    fill_value=0,
                    aggfunc="sum"
                ).reset_index()
                
                # Agregar columna de total
                if "viaje_especifico" in matriz_fecha_pivot.columns and "viaje_parcial" in matriz_fecha_pivot.columns:
                    matriz_fecha_pivot["Total"] = matriz_fecha_pivot["viaje_especifico"] + matriz_fecha_pivot["viaje_parcial"]
                elif "viaje_especifico" in matriz_fecha_pivot.columns:
                    matriz_fecha_pivot["Total"] = matriz_fecha_pivot["viaje_especifico"]
                elif "viaje_parcial" in matriz_fecha_pivot.columns:
                    matriz_fecha_pivot["Total"] = matriz_fecha_pivot["viaje_parcial"]
                
                # Renombrar columnas
                matriz_fecha_pivot = matriz_fecha_pivot.rename(columns={
                    "Fecha_str": "Fecha",
                    "viaje_especifico": "Viajes Específicos",
                    "viaje_parcial": "Viajes Parciales"
                })
                
                # Ordenar por fecha
                if "Fecha" in matriz_fecha_pivot.columns:
                    matriz_fecha_pivot["Fecha_sort"] = pd.to_datetime(matriz_fecha_pivot["Fecha"], format="%d/%m/%Y")
                    matriz_fecha_pivot = matriz_fecha_pivot.sort_values("Fecha_sort").drop("Fecha_sort", axis=1)
                
                st.dataframe(matriz_fecha_pivot, use_container_width=True)
                
                # Gráfico por fecha
                if not matriz_por_fecha.empty:
                    chart_fecha = (
                        alt.Chart(matriz_por_fecha)
                        .mark_bar()
                        .encode(
                            x=alt.X("Fecha_str:N", title="Fecha", sort=None),
                            y=alt.Y("Cantidad:Q", title="Cantidad de Viajes"),
                            color=alt.Color("Proceso:N", 
                                           scale=alt.Scale(domain=["viaje_especifico", "viaje_parcial"], 
                                                         range=["#1f77b4", "#ff7f0e"])),
                            tooltip=["Fecha_str:N", "Proceso:N", "Cantidad:Q"]
                        )
                        .properties(height=300, title="Secuencias de Viajes por Fecha")
                    )
                    st.altair_chart(chart_fecha, use_container_width=True)
            
            with tab3:
                st.markdown("**🌅 Matriz de Viajes por Turno**")
                
                # Matriz agrupada por turno
                matriz_por_turno = viajes_especificos.groupby(["Turno_str", "Proceso"]).size().reset_index(name="Cantidad")
                
                # Pivot por turno
                matriz_turno_pivot = matriz_por_turno.pivot_table(
                    index="Turno_str",
                    columns="Proceso", 
                    values="Cantidad",
                    fill_value=0,
                    aggfunc="sum"
                ).reset_index()
                
                # Agregar columna de total
                if "viaje_especifico" in matriz_turno_pivot.columns and "viaje_parcial" in matriz_turno_pivot.columns:
                    matriz_turno_pivot["Total"] = matriz_turno_pivot["viaje_especifico"] + matriz_turno_pivot["viaje_parcial"]
                elif "viaje_especifico" in matriz_turno_pivot.columns:
                    matriz_turno_pivot["Total"] = matriz_turno_pivot["viaje_especifico"]
                elif "viaje_parcial" in matriz_turno_pivot.columns:
                    matriz_turno_pivot["Total"] = matriz_turno_pivot["viaje_parcial"]
                
                # Renombrar columnas
                matriz_turno_pivot = matriz_turno_pivot.rename(columns={
                    "Turno_str": "Turno",
                    "viaje_especifico": "Viajes Específicos",
                    "viaje_parcial": "Viajes Parciales"
                })
                
                st.dataframe(matriz_turno_pivot, use_container_width=True)
                
                # Gráfico por turno
                if not matriz_por_turno.empty:
                    chart_turno = (
                        alt.Chart(matriz_por_turno)
                        .mark_bar()
                        .encode(
                            x=alt.X("Turno_str:N", title="Turno"),
                            y=alt.Y("Cantidad:Q", title="Cantidad de Viajes"),
                            color=alt.Color("Proceso:N",
                                           scale=alt.Scale(domain=["viaje_especifico", "viaje_parcial"], 
                                                         range=["#1f77b4", "#ff7f0e"])),
                            tooltip=["Turno_str:N", "Proceso:N", "Cantidad:Q"]
                        )
                        .properties(height=300, title="Secuencias de Viajes por Turno")
                    )
                    st.altair_chart(chart_turno, use_container_width=True)
                
                # Estadísticas adicionales por turno
                st.markdown("**📊 Estadísticas Detalladas por Turno:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Promedio por turno
                    st.markdown("**Promedio de Viajes por Día de Turno:**")
                    dias_unicos = viajes_especificos["Fecha_Turno"].nunique()
                    if dias_unicos > 0:
                        for turno in ["Día", "Noche"]:
                            total_turno = matriz_turno_pivot[matriz_turno_pivot["Turno"] == turno]["Total"].sum() if not matriz_turno_pivot.empty else 0
                            promedio = total_turno / dias_unicos
                            st.metric(f"Promedio {turno}", f"{promedio:.1f} viajes/día")
                
                with col2:
                    # Distribución porcentual
                    st.markdown("**Distribución Porcentual:**")
                    if not matriz_turno_pivot.empty and "Total" in matriz_turno_pivot.columns:
                        total_general = matriz_turno_pivot["Total"].sum()
                        if total_general > 0:
                            for _, row in matriz_turno_pivot.iterrows():
                                porcentaje = (row["Total"] / total_general) * 100
                                st.metric(f"% {row['Turno']}", f"{porcentaje:.1f}%")
            
            with tab4:
                st.markdown("**📅🌅 Matriz Combinada por Fecha y Turno**")
                
                # Crear descripción combinada de fecha-turno
                viajes_especificos["Fecha_Turno_str"] = viajes_especificos["Fecha_str"] + " - " + viajes_especificos["Turno_str"]
                
                # Matriz combinada
                matriz_fecha_turno = viajes_especificos.groupby(["Fecha_Turno_str", "Proceso"]).size().reset_index(name="Cantidad")
                
                # Pivot combinado
                matriz_ft_pivot = matriz_fecha_turno.pivot_table(
                    index="Fecha_Turno_str",
                    columns="Proceso",
                    values="Cantidad", 
                    fill_value=0,
                    aggfunc="sum"
                ).reset_index()
                
                # Agregar columna de total
                if "viaje_especifico" in matriz_ft_pivot.columns and "viaje_parcial" in matriz_ft_pivot.columns:
                    matriz_ft_pivot["Total"] = matriz_ft_pivot["viaje_especifico"] + matriz_ft_pivot["viaje_parcial"]
                elif "viaje_especifico" in matriz_ft_pivot.columns:
                    matriz_ft_pivot["Total"] = matriz_ft_pivot["viaje_especifico"]
                elif "viaje_parcial" in matriz_ft_pivot.columns:
                    matriz_ft_pivot["Total"] = matriz_ft_pivot["viaje_parcial"]
                
                # Renombrar columnas
                matriz_ft_pivot = matriz_ft_pivot.rename(columns={
                    "Fecha_Turno_str": "Fecha - Turno",
                    "viaje_especifico": "Viajes Específicos",
                    "viaje_parcial": "Viajes Parciales"
                })
                
                st.dataframe(matriz_ft_pivot, use_container_width=True)
                
                # Mostrar detalles con descripción completa de turnos
                st.markdown("**🔍 Vista Detallada con Horarios:**")
                detalle_turnos = viajes_especificos.groupby(["Descripcion_Turno", "Proceso"]).size().reset_index(name="Cantidad")
                detalle_pivot = detalle_turnos.pivot_table(
                    index="Descripcion_Turno",
                    columns="Proceso",
                    values="Cantidad",
                    fill_value=0,
                    aggfunc="sum"
                ).reset_index()
                
                # Agregar total
                if "viaje_especifico" in detalle_pivot.columns and "viaje_parcial" in detalle_pivot.columns:
                    detalle_pivot["Total"] = detalle_pivot["viaje_especifico"] + detalle_pivot["viaje_parcial"]
                elif "viaje_especifico" in detalle_pivot.columns:
                    detalle_pivot["Total"] = detalle_pivot["viaje_especifico"]
                elif "viaje_parcial" in detalle_pivot.columns:
                    detalle_pivot["Total"] = detalle_pivot["viaje_parcial"]
                
                # Renombrar
                detalle_pivot = detalle_pivot.rename(columns={
                    "Descripcion_Turno": "Turno Detallado",
                    "viaje_especifico": "Viajes Específicos",
                    "viaje_parcial": "Viajes Parciales"
                })
                
                st.dataframe(detalle_pivot, use_container_width=True)
            
            with tab5:
                st.markdown("**🚛 Detalle de Viajes por Vehículo con Fecha y Turno**")
                
                # Selector de vehículo para el detalle
                vehiculos_disponibles = sorted(viajes_especificos["Nombre del Vehículo"].unique())
                veh_detalle = st.selectbox("Seleccionar vehículo para detalle:", vehiculos_disponibles, key="veh_detalle")
                
                # Filtrar por vehículo seleccionado
                viajes_veh = viajes_especificos[viajes_especificos["Nombre del Vehículo"] == veh_detalle]
                
                if not viajes_veh.empty:
                    # Sub-tabs para diferentes vistas del vehículo
                    subtab1, subtab2, subtab3 = st.tabs(["📊 Matriz Origen-Destino", "📅 Por Fecha", "🌅 Por Turno"])
                    
                    with subtab1:
                        # Matriz tradicional para el vehículo específico
                        matriz_veh = viajes_veh.groupby(["Origen", "Destino", "Proceso"]).size().reset_index(name="Cantidad")
                        matriz_veh_pivot = matriz_veh.pivot_table(
                            index="Origen", 
                            columns="Destino", 
                            values="Cantidad", 
                            aggfunc="sum", 
                            fill_value=0
                        )
                        
                        st.markdown(f"**Matriz de viajes para {veh_detalle}:**")
                        st.dataframe(matriz_veh_pivot, use_container_width=True)
                    
                    with subtab2:
                        # Análisis por fecha del vehículo
                        st.markdown(f"**Viajes por Fecha - {veh_detalle}:**")
                        viajes_veh_fecha = viajes_veh.groupby(["Fecha_str", "Proceso"]).size().reset_index(name="Cantidad")
                        
                        if not viajes_veh_fecha.empty:
                            pivot_veh_fecha = viajes_veh_fecha.pivot_table(
                                index="Fecha_str",
                                columns="Proceso",
                                values="Cantidad",
                                fill_value=0,
                                aggfunc="sum"
                            ).reset_index()
                            
                            # Agregar total
                            if "viaje_especifico" in pivot_veh_fecha.columns and "viaje_parcial" in pivot_veh_fecha.columns:
                                pivot_veh_fecha["Total"] = pivot_veh_fecha["viaje_especifico"] + pivot_veh_fecha["viaje_parcial"]
                            elif "viaje_especifico" in pivot_veh_fecha.columns:
                                pivot_veh_fecha["Total"] = pivot_veh_fecha["viaje_especifico"]
                            elif "viaje_parcial" in pivot_veh_fecha.columns:
                                pivot_veh_fecha["Total"] = pivot_veh_fecha["viaje_parcial"]
                            
                            pivot_veh_fecha = pivot_veh_fecha.rename(columns={
                                "Fecha_str": "Fecha",
                                "viaje_especifico": "Viajes Específicos", 
                                "viaje_parcial": "Viajes Parciales"
                            })
                            
                            st.dataframe(pivot_veh_fecha, use_container_width=True)
                    
                    with subtab3:
                        # Análisis por turno del vehículo
                        st.markdown(f"**Viajes por Turno - {veh_detalle}:**")
                        viajes_veh_turno = viajes_veh.groupby(["Turno_str", "Proceso"]).size().reset_index(name="Cantidad")
                        
                        if not viajes_veh_turno.empty:
                            pivot_veh_turno = viajes_veh_turno.pivot_table(
                                index="Turno_str",
                                columns="Proceso",
                                values="Cantidad",
                                fill_value=0,
                                aggfunc="sum"
                            ).reset_index()
                            
                            # Agregar total
                            if "viaje_especifico" in pivot_veh_turno.columns and "viaje_parcial" in pivot_veh_turno.columns:
                                pivot_veh_turno["Total"] = pivot_veh_turno["viaje_especifico"] + pivot_veh_turno["viaje_parcial"]
                            elif "viaje_especifico" in pivot_veh_turno.columns:
                                pivot_veh_turno["Total"] = pivot_veh_turno["viaje_especifico"]
                            elif "viaje_parcial" in pivot_veh_turno.columns:
                                pivot_veh_turno["Total"] = pivot_veh_turno["viaje_parcial"]
                            
                            pivot_veh_turno = pivot_veh_turno.rename(columns={
                                "Turno_str": "Turno",
                                "viaje_especifico": "Viajes Específicos",
                                "viaje_parcial": "Viajes Parciales"
                            })
                            
                            st.dataframe(pivot_veh_turno, use_container_width=True)
                    
                    # Estadísticas generales del vehículo
                    st.markdown(f"**📊 Estadísticas Generales - {veh_detalle}:**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        viajes_esp_veh = len(viajes_veh[viajes_veh["Proceso"] == "viaje_especifico"])
                        st.metric("Viajes Específicos", viajes_esp_veh)
                    with col2:
                        viajes_par_veh = len(viajes_veh[viajes_veh["Proceso"] == "viaje_parcial"])
                        st.metric("Viajes Parciales", viajes_par_veh)
                    with col3:
                        dias_activos = viajes_veh["Fecha_Turno"].nunique()
                        st.metric("Días Activos", dias_activos)
                    with col4:
                        total_veh = viajes_esp_veh + viajes_par_veh
                        promedio_dia = total_veh / dias_activos if dias_activos > 0 else 0
                        st.metric("Promedio/Día", f"{promedio_dia:.1f}")
                    
                    # Tabla detallada de viajes del vehículo
                    st.markdown(f"**📋 Detalle Completo de Viajes - {veh_detalle}:**")
                    viajes_detalle = viajes_veh[["Tiempo_entrada", "Origen", "Destino", "Proceso", "Descripcion_Turno"]].copy()
                    viajes_detalle["Tiempo_entrada"] = viajes_detalle["Tiempo_entrada"].dt.strftime("%d/%m/%Y %H:%M")
                    viajes_detalle = viajes_detalle.rename(columns={
                        "Tiempo_entrada": "Fecha-Hora",
                        "Descripcion_Turno": "Turno Detallado"
                    })
                    st.dataframe(viajes_detalle, use_container_width=True)
                
                # Resumen por todos los vehículos con fecha y turno
                st.markdown("**📋 Resumen General por Todos los Vehículos:**")
                resumen_vehiculos = viajes_especificos.groupby(["Nombre del Vehículo", "Proceso"]).size().reset_index(name="Cantidad")
                resumen_pivot = resumen_vehiculos.pivot_table(
                    index="Nombre del Vehículo",
                    columns="Proceso",
                    values="Cantidad",
                    aggfunc="sum",
                    fill_value=0
                )
                
                # Agregar estadísticas adicionales
                resumen_pivot["Total"] = resumen_pivot.sum(axis=1)
                
                # Agregar días activos por vehículo
                dias_por_vehiculo = viajes_especificos.groupby("Nombre del Vehículo")["Fecha_Turno"].nunique().reset_index()
                dias_por_vehiculo.columns = ["Nombre del Vehículo", "Dias_Activos"]
                
                # Merge con resumen
                resumen_pivot = resumen_pivot.reset_index()
                resumen_final = pd.merge(resumen_pivot, dias_por_vehiculo, on="Nombre del Vehículo", how="left")
                
                # Calcular promedio por día
                resumen_final["Promedio_Dia"] = (resumen_final["Total"] / resumen_final["Dias_Activos"]).round(1)
                
                # Ordenar por total descendente
                resumen_final = resumen_final.sort_values("Total", ascending=False)
                
                # Renombrar columnas para presentación
                resumen_final = resumen_final.rename(columns={
                    "Nombre del Vehículo": "Vehículo",
                    "viaje_especifico": "Viajes Específicos",
                    "viaje_parcial": "Viajes Parciales",
                    "Dias_Activos": "Días Activos",
                    "Promedio_Dia": "Prom/Día"
                })
                
                st.dataframe(resumen_final, use_container_width=True)
                
        else:
            st.info("No se encontraron secuencias de viajes entre geocercas específicas con los filtros aplicados.")
    else:
        st.info("No hay transiciones para mostrar la matriz.")

    # ─── SECCIÓN 4: Análisis de Tiempos de Viaje (Simplificado) ────────────────────────
    st.subheader("🚗 Análisis de Tiempos de Viaje")
    
    if not viajes.empty:
        # Estadísticas generales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_viajes = len(viajes)
            st.metric("Total viajes", total_viajes)
        with col2:
            tiempo_promedio = viajes["Duracion_viaje_s"].mean() / 60
            st.metric("Tiempo promedio", f"{tiempo_promedio:.1f} min")
        with col3:
            tiempo_min = viajes["Duracion_viaje_s"].min() / 60
            st.metric("Tiempo mínimo", f"{tiempo_min:.1f} min")
        with col4:
            tiempo_max = viajes["Duracion_viaje_s"].max() / 60
            st.metric("Tiempo máximo", f"{tiempo_max:.1f} min")
        
        # Gráfico de tiempos por vehículo (solo este gráfico)
        st.subheader("🚛 Tiempos de Viaje por Vehículo")
        
        tiempos_vehiculo = viajes.groupby("Nombre del Vehículo").agg({
            "Duracion_viaje_s": ["mean", "count"]
        }).round(2)
        tiempos_vehiculo.columns = ["Tiempo_promedio_s", "Total_viajes"]
        tiempos_vehiculo = tiempos_vehiculo.reset_index()
        tiempos_vehiculo["Tiempo_promedio_min"] = tiempos_vehiculo["Tiempo_promedio_s"] / 60
        
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
        
        # Tabla de métricas por vehículo
        metricas_viaje = construir_metricas_viaje(viajes)
        if not metricas_viaje.empty:
            st.subheader("📋 Métricas Detalladas por Vehículo")
            st.dataframe(metricas_viaje, use_container_width=True)
        
        # Diagnóstico de casos DESCONOCIDO
        st.subheader("🔍 Diagnóstico de Orígenes/Destinos")
        
        # Contar casos desconocidos en los datos actuales
        origen_desconocido = len(viajes[viajes["Origen"] == "DESCONOCIDO"])
        destino_desconocido = len(viajes[viajes["Destino"] == "DESCONOCIDO"])
        ambos_desconocidos = len(viajes[(viajes["Origen"] == "DESCONOCIDO") & (viajes["Destino"] == "DESCONOCIDO")])
        total_viajes = len(viajes)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Viajes", total_viajes)
        with col2:
            st.metric("Origen Desconocido", origen_desconocido, delta=f"{(origen_desconocido/total_viajes*100):.1f}%" if total_viajes > 0 else "0%")
        with col3:
            st.metric("Destino Desconocido", destino_desconocido, delta=f"{(destino_desconocido/total_viajes*100):.1f}%" if total_viajes > 0 else "0%")
        with col4:
            st.metric("Ambos Desconocidos", ambos_desconocidos, delta=f"{(ambos_desconocidos/total_viajes*100):.1f}%" if total_viajes > 0 else "0%")
        
        # Mostrar detalles de casos problemáticos si existen
        if origen_desconocido > 0 or destino_desconocido > 0:
            with st.expander("🔍 Ver Detalles de Casos DESCONOCIDO"):
                casos_problema = viajes[(viajes["Origen"] == "DESCONOCIDO") | (viajes["Destino"] == "DESCONOCIDO")].copy()
                casos_problema["Inicio_viaje"] = casos_problema["Inicio_viaje"].dt.strftime("%d/%m/%Y %H:%M:%S")
                casos_problema["Fin_viaje"] = casos_problema["Fin_viaje"].dt.strftime("%d/%m/%Y %H:%M:%S")
                casos_problema["Duracion_min"] = (casos_problema["Duracion_viaje_s"] / 60).round(1)
                
                st.markdown("**Posibles causas de casos DESCONOCIDO:**")
                st.info("""
                - **Inicio de dataset**: Viajes al comienzo del período sin geocerca anterior
                - **Final de dataset**: Viajes al final del período sin geocerca posterior  
                - **Datos incompletos**: Períodos largos sin registros de geocercas
                - **Filtrado de GPS**: Geocercas muy cortas filtradas por ruido GPS
                """)
                
                # Renombrar para mejor visualización
                casos_display = casos_problema[["Nombre del Vehículo", "Origen", "Destino", "Inicio_viaje", "Fin_viaje", "Duracion_min", "Descripcion_Turno"]].copy()
                casos_display = casos_display.rename(columns={
                    "Descripcion_Turno": "Turno Detallado"
                })
                st.dataframe(casos_display, use_container_width=True)
        else:
            st.success("✅ Todos los viajes tienen origen y destino identificados correctamente")
            
    else:
        st.info("No se detectaron viajes en el período seleccionado.")

    # ─── SECCIÓN 5: Mapa de Calor - Zonas No Mapeadas ────────────────────────
    st.subheader("🗺️ Análisis de Zonas No Mapeadas")
    
    st.info("""
    **🎯 Funcionalidad de Detección de Zonas:**
    - Identifica áreas donde los vehículos permanecen mucho tiempo fuera de geocercas conocidas
    - Detecta patrones de baja velocidad que sugieren actividad operacional
    - Ayuda a descubrir geocercas potenciales no mapeadas en el sistema
    """)
    
    # Controles para el análisis
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        velocidad_max = st.slider("Velocidad máxima (km/h)", 0, 20, 5, help="Velocidad máxima para considerar como 'parado'")
    with col2:
        tiempo_min = st.slider("Tiempo mínimo (minutos)", 5, 60, 10, help="Tiempo mínimo de permanencia para considerar como zona candidata")
    with col3:
        radio_agrupacion = st.slider("Radio agrupación (metros)", 5, 50, 10, help="Radio para agrupar zonas cercanas")
    with col4:
        mostrar_mapa = st.checkbox("Mostrar mapa interactivo", value=True)
    
    # Analizar zonas candidatas
    zonas_candidatas = analizar_zonas_no_mapeadas(df_filtrado, velocidad_max, tiempo_min, radio_agrupacion)
    
    if not zonas_candidatas.empty:
        # Estadísticas de zonas encontradas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Zonas Detectadas", len(zonas_candidatas))
        with col2:
            duracion_total = zonas_candidatas["Duracion_Minutos"].sum()
            st.metric("Tiempo Total", f"{duracion_total:.0f} min")
        with col3:
            duracion_promedio = zonas_candidatas["Duracion_Minutos"].mean()
            st.metric("Duración Promedio", f"{duracion_promedio:.1f} min")
        with col4:
            vehiculos_afectados = zonas_candidatas["Nombre del Vehículo"].nunique()
            st.metric("Vehículos Involucrados", vehiculos_afectados)
        
        # Tabla de zonas candidatas
        st.markdown("**📋 Zonas Candidatas Detectadas (Agrupadas):**")
        zonas_display = zonas_candidatas.copy()
        zonas_display["Inicio"] = zonas_display["Inicio"].dt.strftime("%d/%m/%Y %H:%M")
        zonas_display["Fin"] = zonas_display["Fin"].dt.strftime("%d/%m/%Y %H:%M")
        zonas_display["Duracion_Minutos"] = zonas_display["Duracion_Minutos"].round(1)
        zonas_display["Radio_Aprox_m"] = zonas_display["Radio_Aprox_m"].round(0)
        zonas_display["Velocidad_Promedio"] = zonas_display["Velocidad_Promedio"].round(1)
        
        # Preparar información de agrupación
        if "Zonas_Agrupadas" in zonas_display.columns:
            zonas_display["Info_Agrupacion"] = zonas_display.apply(
                lambda row: f"{row['Zonas_Agrupadas']} zonas" if row.get('Zonas_Agrupadas', 1) > 1 else "Individual", axis=1
            )
        else:
            zonas_display["Info_Agrupacion"] = "Individual"
        
        # Preparar lista de vehículos
        if "Vehiculos_Involucrados" in zonas_display.columns:
            zonas_display["Vehiculos_Lista"] = zonas_display["Vehiculos_Involucrados"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x)
            )
        else:
            zonas_display["Vehiculos_Lista"] = zonas_display["Nombre del Vehículo"]
        
        # Renombrar columnas para mejor visualización
        zonas_display = zonas_display.rename(columns={
            "Nombre del Vehículo": "Tipo",
            "Latitud_Centro": "Latitud",
            "Longitud_Centro": "Longitud", 
            "Duracion_Minutos": "Duración (min)",
            "Radio_Aprox_m": "Radio (m)",
            "Velocidad_Promedio": "Vel. Prom (km/h)",
            "Info_Agrupacion": "Agrupación",
            "Vehiculos_Lista": "Vehículos"
        })
        
        # Mostrar tabla con información de agrupación
        columnas_mostrar = ["Tipo", "Agrupación", "Vehículos", "Latitud", "Longitud", "Duración (min)", "Registros", "Radio (m)", "Vel. Prom (km/h)", "Inicio", "Fin"]
        columnas_disponibles = [col for col in columnas_mostrar if col in zonas_display.columns]
        st.dataframe(zonas_display[columnas_disponibles], use_container_width=True)
        
        # Mostrar información adicional sobre agrupación
        zonas_agrupadas = zonas_candidatas[zonas_candidatas.get("Zonas_Agrupadas", 1) > 1] if "Zonas_Agrupadas" in zonas_candidatas.columns else pd.DataFrame()
        if not zonas_agrupadas.empty:
            st.info(f"""
            **🔗 Agrupación Aplicada:**
            - Radio de agrupación: {radio_agrupacion} metros
            - {len(zonas_agrupadas)} zonas agrupadas de un total de {len(zonas_candidatas)}
            - Zonas individuales: {len(zonas_candidatas) - len(zonas_agrupadas)}
            """)
        else:
            st.info(f"**📍 Sin agrupación necesaria:** Todas las zonas están separadas por más de {radio_agrupacion} metros")
        
        # Mapa interactivo
        if mostrar_mapa:
            st.markdown("**🗺️ Mapa Interactivo:**")
            try:
                mapa = crear_mapa_calor(df_filtrado, zonas_candidatas)
                st_folium(mapa, width=700, height=500)
                
                st.markdown("""
                **Leyenda del Mapa:**
                - 🟢 **Marcadores Verdes**: Geocercas conocidas y mapeadas
                - 🔴 **Círculos Rojos**: Zonas individuales (un solo vehículo/permanencia)
                - 🟠 **Círculos Naranjas**: Zonas agrupadas (múltiples vehículos/permanencias cercanas)
                - **Tamaño del círculo**: Proporcional al tiempo total de permanencia
                - **Click en círculo**: Ver detalles completos de la zona
                """)
            except Exception as e:
                st.error(f"Error al generar el mapa: {str(e)}")
                st.info("Para ver el mapa, instala las dependencias: `pip install folium streamlit-folium scikit-learn`")
        
        # Recomendaciones
        st.markdown("**💡 Recomendaciones:**")
        zonas_importantes = zonas_candidatas[zonas_candidatas["Duracion_Minutos"] > 30]
        if not zonas_importantes.empty:
            st.warning(f"""
            **🎯 {len(zonas_importantes)} zonas con permanencias largas (>30 min) detectadas:**
            
            Estas zonas podrían ser áreas operacionales importantes no mapeadas como geocercas.
            Considera revisar si corresponden a:
            - Nuevas áreas de trabajo
            - Zonas de mantenimiento
            - Áreas de espera o staging
            - Instalaciones temporales
            """)
        else:
            st.success("✅ No se detectaron zonas con permanencias prolongadas fuera de geocercas conocidas")
            
    else:
        st.success("✅ No se encontraron zonas candidatas con los parámetros seleccionados")
        st.info("Esto puede indicar que todas las áreas operacionales importantes ya están mapeadas como geocercas")





    # ─── SECCIÓN 6: Resumen de Viajes por Vehículo y Geocerca ────────────────────────
    st.subheader("📊 Resumen de Viajes por Vehículo y Geocerca")
    
    if not trans_filtradas.empty:
        # Filtrar solo viajes válidos (específicos y parciales)
        viajes_validos = trans_filtradas[trans_filtradas["Proceso"].isin(["viaje_especifico", "viaje_parcial"])]
        
        if not viajes_validos.empty:
            # Crear resumen por vehículo y geocerca de destino
            resumen_vehiculos_geocercas = viajes_validos.groupby([
                "Nombre del Vehículo", 
                "Destino", 
                "Proceso"
            ]).size().reset_index(name="Cantidad")
            
            # Crear tabla pivot para mejor visualización
            resumen_pivot = resumen_vehiculos_geocercas.pivot_table(
                index=["Nombre del Vehículo", "Destino"],
                columns="Proceso",
                values="Cantidad",
                fill_value=0,
                aggfunc="sum"
            ).reset_index()
            
            # Agregar columna de total
            if "viaje_especifico" in resumen_pivot.columns and "viaje_parcial" in resumen_pivot.columns:
                resumen_pivot["Total"] = resumen_pivot["viaje_especifico"] + resumen_pivot["viaje_parcial"]
            elif "viaje_especifico" in resumen_pivot.columns:
                resumen_pivot["Total"] = resumen_pivot["viaje_especifico"]
            elif "viaje_parcial" in resumen_pivot.columns:
                resumen_pivot["Total"] = resumen_pivot["viaje_parcial"]
            
            # Renombrar columnas para mejor presentación
            resumen_pivot = resumen_pivot.rename(columns={
                "Nombre del Vehículo": "Vehículo",
                "Destino": "Geocerca Destino",
                "viaje_especifico": "Viajes Específicos",
                "viaje_parcial": "Viajes Parciales"
            })
            
            # Ordenar por total descendente
            resumen_pivot = resumen_pivot.sort_values("Total", ascending=False)
            
            st.dataframe(resumen_pivot, use_container_width=True)
            
            # Estadísticas generales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_viajes_esp = resumen_pivot["Viajes Específicos"].sum() if "Viajes Específicos" in resumen_pivot.columns else 0
                st.metric("Total Viajes Específicos", total_viajes_esp)
            with col2:
                total_viajes_par = resumen_pivot["Viajes Parciales"].sum() if "Viajes Parciales" in resumen_pivot.columns else 0
                st.metric("Total Viajes Parciales", total_viajes_par)
            with col3:
                vehiculos_unicos = resumen_pivot["Vehículo"].nunique()
                st.metric("Vehículos Únicos", vehiculos_unicos)
            with col4:
                geocercas_unicas = resumen_pivot["Geocerca Destino"].nunique()
                st.metric("Geocercas Únicas", geocercas_unicas)
            
            # Gráfico de viajes por vehículo
            st.subheader("🚛 Viajes por Vehículo")
            viajes_por_vehiculo = resumen_pivot.groupby("Vehículo")["Total"].sum().reset_index()
            viajes_por_vehiculo = viajes_por_vehiculo.sort_values("Total", ascending=False)
            
            chart_vehiculos = (
                alt.Chart(viajes_por_vehiculo)
                .mark_bar()
                .encode(
                    x=alt.X("Vehículo:N", sort="-y", title="Vehículo"),
                    y=alt.Y("Total:Q", title="Total de Viajes"),
                    tooltip=["Vehículo:N", "Total:Q"]
                )
                .properties(height=300, title="Total de Viajes por Vehículo")
            )
            st.altair_chart(chart_vehiculos, use_container_width=True)
            
            # Gráfico de viajes por geocerca
            st.subheader("🏭 Viajes por Geocerca")
            viajes_por_geocerca = resumen_pivot.groupby("Geocerca Destino")["Total"].sum().reset_index()
            viajes_por_geocerca = viajes_por_geocerca.sort_values("Total", ascending=False)
            
            chart_geocercas = (
                alt.Chart(viajes_por_geocerca)
                .mark_bar()
                .encode(
                    x=alt.X("Geocerca Destino:N", sort="-y", title="Geocerca"),
                    y=alt.Y("Total:Q", title="Total de Viajes"),
                    tooltip=["Geocerca Destino:N", "Total:Q"]
                )
                .properties(height=300, title="Total de Viajes por Geocerca")
            )
            st.altair_chart(chart_geocercas, use_container_width=True)
            
        else:
            st.info("No se encontraron viajes válidos para mostrar el resumen.")
    else:
        st.info("No hay datos de viajes para mostrar el resumen.")

    # ─── Expandir detalles ──────────────────────────────────
    with st.expander("📍 Detalle de transiciones origen → destino"):
        if not trans_filtradas.empty:
            # Reordenar columnas para mejor visualización
            columnas_mostrar = [
                "Nombre del Vehículo", "Origen", "Destino", "Proceso",
                "Tiempo_entrada", "Tiempo_salida", "Duracion_s", 
                "Descripcion_Turno", "Fecha_Turno"
            ]
            trans_display = trans_filtradas.copy()
            trans_display["Tiempo_entrada"] = trans_display["Tiempo_entrada"].dt.strftime("%d/%m/%Y %H:%M:%S")
            trans_display["Tiempo_salida"] = trans_display["Tiempo_salida"].dt.strftime("%d/%m/%Y %H:%M:%S")
            trans_display["Fecha_Turno"] = trans_display["Fecha_Turno"].dt.strftime("%d/%m/%Y")
            
            # Mostrar solo las columnas que existen
            columnas_existentes = [col for col in columnas_mostrar if col in trans_display.columns]
            st.dataframe(trans_display[columnas_existentes], use_container_width=True)
        else:
            st.info("Sin transiciones disponibles")

    with st.expander("🚗 Detalle de tiempos de viaje"):
        if not viajes.empty:
            # Reordenar columnas para mejor visualización
            viajes_display = viajes.copy()
            viajes_display["Inicio_viaje"] = viajes_display["Inicio_viaje"].dt.strftime("%d/%m/%Y %H:%M:%S")
            viajes_display["Fin_viaje"] = viajes_display["Fin_viaje"].dt.strftime("%d/%m/%Y %H:%M:%S")
            viajes_display["Fecha_Turno"] = viajes_display["Fecha_Turno"].dt.strftime("%d/%m/%Y")
            viajes_display["Duracion_min"] = (viajes_display["Duracion_viaje_s"] / 60).round(1)
            
            columnas_viajes = [
                "Nombre del Vehículo", "Origen", "Destino",
                "Inicio_viaje", "Fin_viaje", "Duracion_min", "Duracion_viaje_s",
                "Descripcion_Turno", "Fecha_Turno"
            ]
            columnas_existentes = [col for col in columnas_viajes if col in viajes_display.columns]
            st.dataframe(viajes_display[columnas_existentes], use_container_width=True)
        else:
            st.info("Sin viajes detectados")
    
    # Nuevo expandible con información detallada de turnos
    with st.expander("⏰ Información Detallada de Turnos"):
        st.markdown("""
        **🌅 Definición de Turnos Mejorada:**
        
        **Turno Día:**
        - Horario: 08:00 - 19:59
        - La fecha del turno corresponde al mismo día
        - Ejemplo: Turno Día 31-07-2025 (08:00-19:59 del 31-07-2025)
        
        **Turno Noche:**
        - Horario: 20:00 - 07:59 (del día siguiente)
        - La fecha del turno corresponde al día que INICIA el turno
        - Ejemplo: Turno Noche 31-07-2025 (20:00 del 31-07-2025 - 07:59 del 01-08-2025)
        
        **📊 Ejemplos de Consultas:**
        - "¿Cuántos viajes hizo el vehículo X en el turno de noche del día 31-07-2025?"
          → Se incluyen viajes desde 20:00 del 31-07-2025 hasta 07:59 del 01-08-2025
        - "¿Cuántas cargas se realizaron en el turno día del 01-08-2025?"
          → Se incluyen cargas desde 08:00 hasta 19:59 del 01-08-2025
        """)
        
        # Mostrar estadísticas de turnos si hay datos
        if not trans_filtradas.empty:
            st.markdown("**📈 Estadísticas de Turnos en Datos Filtrados:**")
            
            # Contar por tipo de turno y fecha
            stats_turnos = trans_filtradas.groupby(["Descripcion_Turno", "Proceso"]).size().reset_index(name="Cantidad")
            
            if not stats_turnos.empty:
                # Crear tabla pivot
                stats_pivot = stats_turnos.pivot_table(
                    index="Descripcion_Turno",
                    columns="Proceso", 
                    values="Cantidad",
                    fill_value=0,
                    aggfunc="sum"
                ).reset_index()
                
                st.dataframe(stats_pivot, use_container_width=True)
            
            # Mostrar resumen de fechas únicas por turno
            st.markdown("**📅 Fechas Únicas por Tipo de Turno:**")
            fechas_turno = trans_filtradas.groupby("Turno")["Fecha_Turno"].nunique().reset_index()
            fechas_turno.columns = ["Tipo de Turno", "Días Únicos"]
            fechas_turno["Tipo de Turno"] = fechas_turno["Tipo de Turno"].map({"dia": "Día", "noche": "Noche"})
            st.dataframe(fechas_turno, use_container_width=True)

    # ─── Exportar a Excel ───────────────────────────────────
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
        if not trans_filtradas.empty:
            trans_filtradas.to_excel(excel_writer=xls, sheet_name="Transiciones", index=False)
        if not viajes.empty:
            viajes.to_excel(excel_writer=xls, sheet_name="TiemposViaje", index=False)
        if not viajes.empty:
            metricas_viaje = construir_metricas_viaje(viajes)
            if not metricas_viaje.empty:
                metricas_viaje.to_excel(excel_writer=xls, sheet_name="MetricasViaje", index=False)
    
    st.download_button("💾 Descargar reporte Excel",
                       buf.getvalue(),
                       "reporte_operacional_filtrado.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")