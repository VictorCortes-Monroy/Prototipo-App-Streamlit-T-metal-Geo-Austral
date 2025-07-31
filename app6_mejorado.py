"""
Streamlit - T-Metal · BI Operacional + Análisis de Tiempos de Viaje - MEJORADO
Versión 2025-01-31 – Dashboard reorganizado con:
• Filtros por geocerca origen y destino
• Matriz de viajes de carga/descarga
• Análisis de tiempos de viaje optimizado
• Eliminación de gráficos innecesarios
• Sin métricas de productividad
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
    page_title="⛏️ T-Metal – BI Operacional + Tiempos de Viaje",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# Parámetros globales
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
# Funciones copiadas de app6
# ─────────────────────────────────────────────────────────────
def turno(ts: pd.Timestamp) -> str:
    h = ts.time()
    return "dia" if SHIFT_DAY_START <= h < SHIFT_NIGHT_START else "noche"

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
    """Detecta automáticamente los dominios de geocercas."""
    global STOCKS, MODULES, BOTADEROS, PILAS_ROM
    
    geos = set(df["Geocercas"].unique()) - {""}
    
    STOCKS = {g for g in geos if "stock" in normalizar(g)}
    MODULES = {g for g in geos if "modulo" in normalizar(g) or "módulo" in normalizar(g)}
    BOTADEROS = {g for g in geos if "botadero" in normalizar(g)}
    PILAS_ROM = {g for g in geos if "pila" in normalizar(g) and "rom" in normalizar(g)}
    
    # Detectar instalaciones de faena
    INSTALACIONES_FAENA = {g for g in geos if "instalacion" in normalizar(g) or "faena" in normalizar(g)}
    CASINO = {g for g in geos if "casino" in normalizar(g)}
    # Geocercas no operacionales (cualquier viaje hacia/desde estas es clasificado como "otro")
    GEOCERCAS_NO_OPERACIONALES = INSTALACIONES_FAENA | CASINO
    
    globals()["INSTALACIONES_FAENA"] = INSTALACIONES_FAENA
    globals()["CASINO"] = CASINO
    globals()["GEOCERCAS_NO_OPERACIONALES"] = GEOCERCAS_NO_OPERACIONALES

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
            
            transiciones_completas.append({
                "Nombre del Vehículo": veh,
                "Origen": origen,
                "Destino": destino,
                "Tiempo_entrada": tiempos_entrada[i],
                "Tiempo_salida": tiempo_salida_origen,
                "Duracion_s": duracion_permanencia,
                "Turno": turno(tiempos_entrada[i])
            })

    if transiciones_completas:
        return pd.DataFrame(transiciones_completas)
    else:
        return pd.DataFrame(columns=[
            "Nombre del Vehículo", "Origen", "Destino",
            "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"
        ])

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

    df = df.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    df["Proceso"] = "otro"  # Inicializar todos como "otro"

    # Obtener geocercas no operacionales del contexto global
    GEOCERCAS_NO_OPERACIONALES = globals().get("GEOCERCAS_NO_OPERACIONALES", set())

    # Procesar cada vehículo por separado
    grupos_procesados = []

    for veh, grupo in df.groupby("Nombre del Vehículo"):
        grupo = grupo.copy().sort_values("Tiempo_entrada").reset_index(drop=True)

        for i in range(len(grupo)):
            origen = grupo.loc[i, "Origen"]
            destino = grupo.loc[i, "Destino"]

            # 🏭 PRIORIDAD ALTA: Movimientos que involucran geocercas no operacionales son "otros"
            if origen in GEOCERCAS_NO_OPERACIONALES or destino in GEOCERCAS_NO_OPERACIONALES:
                grupo.loc[i, "Proceso"] = "otro"
                continue

            # 1. CARGA: Stock → Módulo/Pila ROM
            if origen in STOCKS and (destino in MODULES or destino in PILAS_ROM):
                grupo.loc[i, "Proceso"] = "carga"
                continue

            # 2. DESCARGA: Módulo/Pila ROM → Botadero
            if (origen in MODULES or origen in PILAS_ROM) and destino in BOTADEROS:
                grupo.loc[i, "Proceso"] = "descarga"
                continue

            # 3. RETORNO: Botadero → Módulo/Pila ROM (después de descarga)
            if origen in BOTADEROS and (destino in MODULES or destino in PILAS_ROM):
                if i > 0:
                    viaje_anterior = grupo.loc[i-1, "Proceso"]
                    if viaje_anterior == "descarga":
                        grupo.loc[i, "Proceso"] = "retorno"
                        continue
                grupo.loc[i, "Proceso"] = "otro"
                continue

            # 4. RETORNO: Módulo/Pila ROM → Stock (después de carga)
            if (origen in MODULES or origen in PILAS_ROM) and destino in STOCKS:
                if i > 0:
                    viaje_anterior = grupo.loc[i-1, "Proceso"]
                    if viaje_anterior == "carga":
                        grupo.loc[i, "Proceso"] = "retorno"
                        continue
                grupo.loc[i, "Proceso"] = "otro"
                continue

        grupos_procesados.append(grupo)

    if grupos_procesados:
        return pd.concat(grupos_procesados, ignore_index=True)
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
            
            viajes.append({
                "Nombre del Vehículo": veh,
                "Origen": origen,
                "Destino": destino,
                "Inicio_viaje": inicio,
                "Fin_viaje": fin,
                "Duracion_viaje_s": duracion_s,
                "Turno": turno(inicio)
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
            "Inicio_viaje", "Fin_viaje", "Duracion_viaje_s", "Turno"
        ])

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
st.header("📤 Carga de archivo CSV – Eventos GPS + Análisis de Tiempos de Viaje")
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
    
    # ─── SECCIÓN 1: Geocercas Detectadas ────────────────────────
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
        
        st.markdown("**🍽️ Casino:**")
        CASINO = globals().get("CASINO", set())
        if CASINO:
            for casino in sorted(CASINO):
                st.write(f"• {casino}")
        else:
            st.write("Ninguna detectada")
    
    # Mostrar geocercas no clasificadas
    GEOCERCAS_NO_OPERACIONALES = globals().get("GEOCERCAS_NO_OPERACIONALES", set())
    geocercas_clasificadas = STOCKS | MODULES | BOTADEROS | PILAS_ROM | GEOCERCAS_NO_OPERACIONALES
    geocercas_no_clasificadas = set(df["Geocercas"].unique()) - {""} - geocercas_clasificadas
    
    if geocercas_no_clasificadas:
        st.warning(f"""
        **❓ Geocercas No Clasificadas ({len(geocercas_no_clasificadas)}):**
        {', '.join(sorted(geocercas_no_clasificadas))}
        """)
    else:
        st.success("✅ Todas las geocercas fueron clasificadas correctamente")

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
        # Filtro de turno
        turno_opts = ["Todos", "Día", "Noche"]
        turno_sel = st.selectbox("Turno", turno_opts)
    
    with col4:
        # Filtro de geocerca origen
        todas_geocercas = sorted(set(df["Geocercas"].unique()) - {""})
        origen_opts = ["Todas"] + todas_geocercas
        origen_sel = st.selectbox("Geocerca Origen", origen_opts)
    
    with col5:
        # Filtro de geocerca destino
        destino_opts = ["Todas"] + todas_geocercas
        destino_sel = st.selectbox("Geocerca Destino", destino_opts)

    # Aplicar filtros a los datos
    df_filtrado = df[(df["Tiempo de evento"].dt.date >= rango[0]) & 
                     (df["Tiempo de evento"].dt.date <= rango[1])]
    
    if veh_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nombre del Vehículo"] == veh_sel]
    
    if turno_sel != "Todos":
        turno_filter = "dia" if turno_sel == "Día" else "noche"
        df_filtrado = df_filtrado[df_filtrado["Tiempo de evento"].apply(turno) == turno_filter]
    
    # Procesar datos filtrados
    trans = extraer_transiciones(df_filtrado)
    viajes = extraer_tiempos_viaje(df_filtrado)
    
    if not trans.empty:
        trans = clasificar_proceso_con_secuencia(trans)
    
    # Filtrar transiciones por origen y destino
    trans_filtradas = trans.copy()
    if not trans_filtradas.empty:
        if origen_sel != "Todas":
            trans_filtradas = trans_filtradas[trans_filtradas["Origen"] == origen_sel]
        if destino_sel != "Todas":
            trans_filtradas = trans_filtradas[trans_filtradas["Destino"] == destino_sel]

    # ─── SECCIÓN 3: Matriz de Viajes de Carga/Descarga ────────────────────────
    st.subheader("📊 Matriz de Viajes de Producción (Carga/Descarga)")
    
    if not trans_filtradas.empty:
        viajes_produccion = trans_filtradas[trans_filtradas["Proceso"].isin(["carga", "descarga"])]
        
        if not viajes_produccion.empty:
            # Tabs para mostrar matriz general y por vehículo
            tab1, tab2 = st.tabs(["📊 Matriz General", "🚛 Detalle por Vehículo"])
            
            with tab1:
                st.markdown("**Matriz General de Viajes Origen → Destino**")
                
                # Crear matriz de origen-destino general
                matriz_viajes = viajes_produccion.groupby(["Origen", "Destino", "Proceso"]).size().reset_index(name="Cantidad")
                
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
                    total_carga = len(viajes_produccion[viajes_produccion["Proceso"] == "carga"])
                    st.metric("Total Cargas", total_carga)
                with col2:
                    total_descarga = len(viajes_produccion[viajes_produccion["Proceso"] == "descarga"])
                    st.metric("Total Descargas", total_descarga)
                with col3:
                    total_produccion = total_carga + total_descarga
                    st.metric("Total Producción", total_produccion)
            
            with tab2:
                st.markdown("**Detalle de Viajes por Vehículo**")
                
                # Selector de vehículo para el detalle
                vehiculos_disponibles = sorted(viajes_produccion["Nombre del Vehículo"].unique())
                veh_detalle = st.selectbox("Seleccionar vehículo para detalle:", vehiculos_disponibles, key="veh_detalle")
                
                # Filtrar por vehículo seleccionado
                viajes_veh = viajes_produccion[viajes_produccion["Nombre del Vehículo"] == veh_detalle]
                
                if not viajes_veh.empty:
                    # Matriz para el vehículo específico
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
                    
                    # Estadísticas por vehículo
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        carga_veh = len(viajes_veh[viajes_veh["Proceso"] == "carga"])
                        st.metric(f"Cargas - {veh_detalle}", carga_veh)
                    with col2:
                        descarga_veh = len(viajes_veh[viajes_veh["Proceso"] == "descarga"])
                        st.metric(f"Descargas - {veh_detalle}", descarga_veh)
                    with col3:
                        total_veh = carga_veh + descarga_veh
                        st.metric(f"Total - {veh_detalle}", total_veh)
                    
                    # Tabla detallada de viajes del vehículo
                    st.markdown(f"**Detalle completo de viajes - {veh_detalle}:**")
                    viajes_detalle = viajes_veh[["Tiempo_entrada", "Origen", "Destino", "Proceso", "Turno"]].copy()
                    viajes_detalle["Tiempo_entrada"] = viajes_detalle["Tiempo_entrada"].dt.strftime("%d/%m/%Y %H:%M")
                    st.dataframe(viajes_detalle, use_container_width=True)
                
                # Resumen por todos los vehículos
                st.markdown("**📋 Resumen por Todos los Vehículos:**")
                resumen_vehiculos = viajes_produccion.groupby(["Nombre del Vehículo", "Proceso"]).size().reset_index(name="Cantidad")
                resumen_pivot = resumen_vehiculos.pivot_table(
                    index="Nombre del Vehículo",
                    columns="Proceso",
                    values="Cantidad",
                    aggfunc="sum",
                    fill_value=0
                )
                
                # Agregar columna de total
                resumen_pivot["Total"] = resumen_pivot.sum(axis=1)
                
                # Ordenar por total descendente
                resumen_pivot = resumen_pivot.sort_values("Total", ascending=False)
                
                st.dataframe(resumen_pivot, use_container_width=True)
                
        else:
            st.info("No se encontraron viajes de producción con los filtros aplicados.")
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
                
                st.dataframe(casos_problema[["Nombre del Vehículo", "Origen", "Destino", "Inicio_viaje", "Fin_viaje", "Duracion_min", "Turno"]], use_container_width=True)
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

    # ─── SECCIÓN 6: Producción Horaria ────────────────────────
    st.subheader("🔋 Producción Horaria")
    
    if not trans_filtradas.empty:
        viajes_produccion_hora = trans_filtradas[trans_filtradas["Proceso"].isin(["carga", "descarga"])].copy()
        
        if not viajes_produccion_hora.empty:
            viajes_produccion_hora["Hora_cal"] = viajes_produccion_hora["Tiempo_entrada"].dt.floor("h")
            
            # Agrupar por hora y proceso
            viajes_agrupados = viajes_produccion_hora.groupby(["Hora_cal", "Proceso"]).size().reset_index(name="Cantidad")
            
            # Gráfico de producción horaria
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
        else:
            st.info("No hay viajes de producción para mostrar.")
    else:
        st.info("No hay datos de producción para mostrar.")

    # ─── SECCIÓN 6: Toneladas Estimadas ────────────────────────
    st.subheader("🪨 Toneladas Acumuladas (Estimadas)")
    
    if not trans_filtradas.empty:
        viajes_produccion_tons = trans_filtradas[trans_filtradas["Proceso"].isin(["carga", "descarga"])].copy()
        
        if not viajes_produccion_tons.empty:
            # Asignar promedio fijo de 42 toneladas por viaje de producción
            viajes_produccion_tons["Toneladas"] = 42.0

            # Agrupar por hora y tipo de proceso
            tons_h = (
                viajes_produccion_tons.groupby([
                    viajes_produccion_tons["Tiempo_entrada"].dt.floor("h"),
                    "Proceso"
                ])["Toneladas"].sum().reset_index()
                .rename(columns={"Tiempo_entrada": "Hora_cal", "Toneladas": "Toneladas_h"})
            )

            # Gráfico de toneladas
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
                toneladas_carga = viajes_produccion_tons[viajes_produccion_tons["Proceso"] == "carga"]["Toneladas"].sum()
                st.metric("Toneladas carga", f"{toneladas_carga:.1f} t")
            with col2:
                toneladas_descarga = viajes_produccion_tons[viajes_produccion_tons["Proceso"] == "descarga"]["Toneladas"].sum()
                st.metric("Toneladas descarga", f"{toneladas_descarga:.1f} t")
            with col3:
                toneladas_total = viajes_produccion_tons["Toneladas"].sum()
                st.metric("Toneladas total", f"{toneladas_total:.1f} t")
        else:
            st.info("Sin viajes de producción – no se estiman toneladas.")
    else:
        st.info("No hay datos para estimar toneladas.")

    # ─── SECCIÓN 7: Resumen de Viajes por Tipo ────────────────────────
    st.subheader("📊 Resumen de Viajes por Tipo")
    
    if not trans_filtradas.empty:
        # Contar por tipo de proceso
        conteo_procesos = trans_filtradas["Proceso"].value_counts()
        
        # Crear DataFrame con información detallada
        resumen_viajes = pd.DataFrame({
            "Tipo de Viaje": ["Carga", "Descarga", "Retorno", "Otros"],
            "Cantidad": [
                conteo_procesos.get("carga", 0),
                conteo_procesos.get("descarga", 0),
                conteo_procesos.get("retorno", 0),
                conteo_procesos.get("otro", 0)
            ]
        })
        
        # Agregar porcentajes
        total_viajes = resumen_viajes["Cantidad"].sum()
        if total_viajes > 0:
            resumen_viajes["Porcentaje"] = (resumen_viajes["Cantidad"] / total_viajes * 100).round(1)
        else:
            resumen_viajes["Porcentaje"] = 0
        
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
    else:
        st.info("No hay datos de viajes para mostrar el resumen.")

    # ─── Expandir detalles ──────────────────────────────────
    with st.expander("📍 Detalle de transiciones origen → destino"):
        if not trans_filtradas.empty:
            st.dataframe(trans_filtradas, use_container_width=True)
        else:
            st.info("Sin transiciones disponibles")

    with st.expander("🚗 Detalle de tiempos de viaje"):
        if not viajes.empty:
            st.dataframe(viajes, use_container_width=True)
        else:
            st.info("Sin viajes detectados")

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