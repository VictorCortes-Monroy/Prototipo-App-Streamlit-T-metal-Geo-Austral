import streamlit as st
import pandas as pd
import numpy as np
from datetime import time
from io import BytesIO

st.set_page_config(layout="wide", page_title="⛏️ T‑Metal – BI Operacional")

# ============================================================
# 0) Parámetros generales
# ============================================================
MIN_ESTANCIA_S = 60              # estadía mínima para contar transiciones (seg)
SHIFT_DAY_START  = time(8, 0)    # 08:00 ⇒ turno día
SHIFT_NIGHT_START = time(20, 0)  # 20:00 ⇒ turno noche

# → Conjuntos de geocercas (rellenos dinámicamente)
STOCKS: set[str]    = set()
MODULES: set[str]   = set()
BOTADEROS: set[str] = set()

# ============================================================
# 1) Utilidades
# ============================================================

def turno(ts: pd.Timestamp) -> str:
    h = ts.time()
    return "dia" if SHIFT_DAY_START <= h < SHIFT_NIGHT_START else "noche"


def preparar_datos(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df["Tiempo de evento"] = pd.to_datetime(df["Tiempo de evento"], errors="coerce")
    df.dropna(subset=["Tiempo de evento"], inplace=True)
    df["Geocerca"] = df["Geocercas"].fillna("").str.strip()
    df.sort_values(["Nombre del Vehículo", "Tiempo de evento"], inplace=True)
    return df


def poblar_dominios(df: pd.DataFrame) -> None:
    global STOCKS, MODULES, BOTADEROS
    geos = set(df["Geocerca"].unique()) - {""}
    STOCKS    = {g for g in geos if "stock"    in g.lower()}
    MODULES   = {g for g in geos if "modulo"   in g.lower()}
    BOTADEROS = {g for g in geos if "botadero" in g.lower() or g.lower().startswith("botadero")}
    if not BOTADEROS:
        BOTADEROS = {"Botaderos"}

# ============================================================
# 2) Extracción de transiciones
# ============================================================

def extraer_transiciones(df: pd.DataFrame) -> pd.DataFrame:
    registros: list[pd.DataFrame] = []
    for veh, g in df.groupby("Nombre del Vehículo"):
        g_valid = g[g["Geocerca"] != ""].copy()
        if g_valid.empty:
            continue
        g_valid["Geo_next"]  = g_valid["Geocerca"].shift(-1)
        g_valid["Time_next"] = g_valid["Tiempo de evento"].shift(-1)
        cambios = g_valid[g_valid["Geo_next"].notna() & (g_valid["Geocerca"] != g_valid["Geo_next"])].copy()
        if cambios.empty:
            continue
        cambios["Duracion_s"] = (cambios["Time_next"] - cambios["Tiempo de evento"]).dt.total_seconds()
        cambios = cambios[cambios["Duracion_s"] >= MIN_ESTANCIA_S]
        if cambios.empty:
            continue
        cambios["Origen"]         = cambios["Geocerca"]
        cambios["Destino"]        = cambios["Geo_next"]
        cambios["Tiempo_entrada"] = cambios["Tiempo de evento"]
        cambios["Tiempo_salida"]  = cambios["Time_next"]
        cambios["Turno"]          = cambios["Tiempo_entrada"].apply(turno)
        registros.append(
            cambios[["Nombre del Vehículo", "Origen", "Destino", "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"]]
        )
    return pd.concat(registros, ignore_index=True) if registros else pd.DataFrame(columns=[
        "Nombre del Vehículo", "Origen", "Destino", "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"])

# ============================================================
# 3) Clasificación de procesos
# ============================================================

def clasificar_proceso(row: pd.Series) -> str:
    orig, dest = row["Origen"], row["Destino"]
    if orig in STOCKS and dest in MODULES:
        return "carga"
    if orig in MODULES and dest in STOCKS:
        return "retorno"
    if orig in MODULES and dest in BOTADEROS:
        return "descarga"
    return "otro"

# ============================================================
# 4) Ciclos Stock→Módulo→Stock
# ============================================================

def detectar_ciclos(trans: pd.DataFrame) -> pd.DataFrame:
    if trans.empty:
        return pd.DataFrame()
    t = trans.sort_values(["Nombre del Vehículo", "Tiempo_entrada"]).copy()
    t["Proceso"]    = t.apply(clasificar_proceso, axis=1)
    t["Proc_next"]  = t.groupby("Nombre del Vehículo")["Proceso"].shift(-1)
    mask = (t["Proceso"] == "carga") & (t["Proc_next"] == "retorno")
    ciclos = t[mask].copy()
    ciclos["Ciclo_ID"] = np.arange(len(ciclos))
    return ciclos

# ============================================================
# 5) Métricas agregadas
# ============================================================

def construir_metricas(trans: pd.DataFrame, ciclos: pd.DataFrame):
    if trans.empty:
        vacio = pd.DataFrame()
        return vacio, ciclos, vacio
    trans = trans.copy()
    trans["Proceso"] = trans.apply(clasificar_proceso, axis=1)
    trans["Hora_cal"] = trans["Tiempo_entrada"].dt.floor("h")  # «h» en vez de «H»
    viajes_h = (
        trans.groupby(["Hora_cal", "Proceso"]).size().unstack(fill_value=0).reset_index()
    )
    trans["Duracion_h"] = trans["Duracion_s"] / 3600
    actividad = (
        trans.groupby([trans["Tiempo_entrada"].dt.date.rename("Fecha"), "Nombre del Vehículo"])["Duracion_h"].sum().reset_index()
    )
    return viajes_h, ciclos, actividad

# ============================================================
# 6) UI Streamlit
# ============================================================

st.header("📤 Carga de archivo CSV – Eventos GPS")
archivo = st.file_uploader("Selecciona el CSV exportado desde GeoAustral", type=["csv"])

if archivo:
    raw = pd.read_csv(archivo)
    df  = preparar_datos(raw)
    poblar_dominios(df)

    # --- Filtro fecha
    f_min, f_max = df["Tiempo de evento"].min().date(), df["Tiempo de evento"].max().date()
    rango = st.date_input("Rango de fechas", [f_min, f_max])
    df = df[(df["Tiempo de evento"].dt.date >= rango[0]) & (df["Tiempo de evento"].dt.date <= rango[1])]

    # --- Filtro vehículo
    veh_opts = ["Todos"] + sorted(df["Nombre del Vehículo"].unique())
    veh_sel = st.selectbox("Vehículo", veh_opts)
    if veh_sel != "Todos":
        df = df[df["Nombre del Vehículo"] == veh_sel]

    # --- Procesamiento
    trans = extraer_transiciones(df)
    ciclos = detectar_ciclos(trans)
    viajes_h, ciclos, actividad = construir_metricas(trans, ciclos)

    # --- Visual
    st.subheader("🚚 Transiciones origen → destino")
    st.dataframe(trans.head(600))

    st.subheader("⏱️ Viajes por hora (carga / retorno / descarga)")
    st.dataframe(viajes_h.head(200))

    st.subheader("🔄 Ciclos detectados (Stock → Módulo → Stock)")
    st.dataframe(ciclos[[
        "Nombre del Vehículo", "Origen", "Destino", "Tiempo_entrada", "Tiempo_salida", "Turno", "Ciclo_ID"
    ]].head(200))

    st.subheader("⚡ Horas activas por vehículo y fecha")
    st.dataframe(actividad)

    # --- Exportar a Excel
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
        trans.to_excel(xls, sheet_name="Transiciones", index=False)
        viajes_h.to_excel(xls, sheet_name="ViajesHora", index=False)
        ciclos.to_excel(xls, sheet_name="Ciclos", index=False)
        actividad.to_excel(xls, sheet_name="Actividad", index=False)

    st.download_button(
        label="💾 Descargar reporte Excel consolidado",
        data=buf.getvalue(),
        file_name="reporte_operacional.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
