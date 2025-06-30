"""
Streamlit - T-Metal · BI Operacional
Versión 2025-06-25 – incluye:
• Producción horaria (viajes de carga)
• Conteo de viajes por tipo
• Ciclos completos por vehículo
• Productividad (% horas de carga vs horas activas)
• Toneladas acumuladas (≈ N(42 t, σ = 3 t) por viaje de carga)
• Exportación a Excel
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import unicodedata
from datetime import time
from io import BytesIO

st.set_page_config(page_title="⛏️ T-Metal – BI Operacional", layout="wide")

# ─────────────────────────────────────────────────────────────
# 0 | Parámetros globales
# ─────────────────────────────────────────────────────────────
MIN_ESTANCIA_S      = 60
SHIFT_DAY_START     = time(8, 0)
SHIFT_NIGHT_START   = time(20, 0)

# Dominios dinámicos
STOCKS: set[str]    = set()
MODULES: set[str]   = set()
BOTADEROS: set[str] = set()


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
    return df


def poblar_dominios(df: pd.DataFrame) -> None:
    """Detecta automáticamente STOCKS, MODULES, BOTADEROS."""
    global STOCKS, MODULES, BOTADEROS
    geos = set(df["Geocerca"].unique()) - {""}
    STOCKS    = {g for g in geos if "stock"    in normalizar(g)}
    MODULES   = {g for g in geos if "modulo"   in normalizar(g)}
    BOTADEROS = {g for g in geos if "botadero" in normalizar(g)} or {"Botaderos"}


# ─────────────────────────────────────────────────────────────
# 2 | Extracción de transiciones geocerca-a-geocerca
# ─────────────────────────────────────────────────────────────
def extraer_transiciones(df: pd.DataFrame) -> pd.DataFrame:
    registros: list[pd.DataFrame] = []
    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g[g["Geocerca"] != ""].copy()
        if g.empty:
            continue
        g["Geo_next"]  = g["Geocerca"].shift(-1)
        g["Time_next"] = g["Tiempo de evento"].shift(-1)

        cambios = g[g["Geo_next"].notna() & (g["Geocerca"] != g["Geo_next"])].copy()
        if cambios.empty:
            continue

        cambios["Duracion_s"] = (cambios["Time_next"] - cambios["Tiempo de evento"]).dt.total_seconds()
        cambios = cambios[cambios["Duracion_s"] >= MIN_ESTANCIA_S]
        if cambios.empty:
            continue

        cambios = cambios.assign(
            Origen=cambios["Geocerca"],
            Destino=cambios["Geo_next"],
            Tiempo_entrada=cambios["Tiempo de evento"],
            Tiempo_salida=cambios["Time_next"],
            Turno=cambios["Tiempo de evento"].apply(turno),
        )
        registros.append(
            cambios[
                ["Nombre del Vehículo", "Origen", "Destino",
                 "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"]
            ]
        )
    if registros:
        return pd.concat(registros, ignore_index=True)
    return pd.DataFrame(columns=[
        "Nombre del Vehículo", "Origen", "Destino",
        "Tiempo_entrada", "Tiempo_salida", "Duracion_s", "Turno"
    ])


# ─────────────────────────────────────────────────────────────
# 3 | Clasificación de proceso
# ─────────────────────────────────────────────────────────────
def clasificar_proceso(row: pd.Series) -> str:
    o, d = row["Origen"], row["Destino"]
    if o in STOCKS   and d in MODULES:   return "carga"
    if o in MODULES  and d in STOCKS:    return "retorno"
    if o in MODULES  and d in BOTADEROS: return "descarga"
    return "otro"


# ─────────────────────────────────────────────────────────────
# 4 | Detección de ciclos Stock→Módulo→Stock
# ─────────────────────────────────────────────────────────────
def detectar_ciclos(trans: pd.DataFrame) -> pd.DataFrame:
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
# 6 | Interfaz Streamlit
# ─────────────────────────────────────────────────────────────
st.header("📤 Carga de archivo CSV – Eventos GPS")
archivo = st.file_uploader("Selecciona el CSV exportado desde GeoAustral", type=["csv"])

if archivo:
    raw = pd.read_csv(archivo)
    df  = preparar_datos(raw)
    poblar_dominios(df)

    # ─── Filtros de fecha y vehículo ────────────────────────
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

    # ─── Procesamiento core ─────────────────────────────────
    trans   = extraer_transiciones(df)
    if trans.empty:
        st.warning("No se encontraron transiciones válidas.")
        st.stop()

    trans["Proceso"] = trans.apply(clasificar_proceso, axis=1)
    ciclos           = detectar_ciclos(trans)
    viajes_h, productividad = construir_metricas(trans)

    # ────────────────────────────────────────────────────────
    #  Dashboard
    # ────────────────────────────────────────────────────────
    st.subheader("🔋 Producción horaria – Viajes de carga")
    if "carga" in viajes_h.columns and not viajes_h["carga"].eq(0).all():
        carga_h = viajes_h[["Hora_cal", "carga"]].rename(columns={"carga": "Viajes_de_carga"})
        chart_carga = (
            alt.Chart(carga_h)
            .mark_line(point=True)
            .encode(x=alt.X("Hora_cal:T", title="Fecha-hora"),
                    y=alt.Y("Viajes_de_carga:Q", title="Viajes de carga"),
                    tooltip=["Hora_cal:T", "Viajes_de_carga"])
            .properties(height=300)
        )
        st.altair_chart(chart_carga, use_container_width=True)
    else:
        st.info("Sin registros de carga en el período seleccionado.")

    # Conteo global de viajes
    st.subheader("📊 Conteo global de viajes (período filtrado)")
    st.dataframe(viajes_h.drop(columns="Hora_cal").sum().to_frame("Total").T)

    # Ciclos completos por vehículo
    st.subheader("🔄 Ciclos completos (Stock→Módulo→Stock)")
    ciclos_tab = (ciclos.groupby("Nombre del Vehículo").size()
                        .reset_index(name="Ciclos")
                        .sort_values("Ciclos", ascending=False))
    st.dataframe(ciclos_tab)

    # ─── Productividad ──────────────────────────────────────
    st.subheader("🚀 Productividad por vehículo")
    prod_fecha = productividad[productividad["Fecha"].between(rango[0], rango[1])]
    if prod_fecha.empty:
        st.info("Sin datos de productividad en el rango.")
    else:
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
    st.subheader("🪨 Toneladas acumuladas (estimadas)")
    carga_trips = trans[trans["Proceso"] == "carga"].copy()
    if carga_trips.empty:
        st.info("Sin viajes de carga – no se estiman toneladas.")
    else:
        np.random.seed(42)
        carga_trips["Toneladas"] = np.random.normal(
            loc=42, scale=3, size=len(carga_trips)
        ).clip(min=0)

        tons_h = (
            carga_trips.groupby(carga_trips["Tiempo_entrada"].dt.floor("h"))["Toneladas"]
                       .sum().reset_index()
                       .rename(columns={"Tiempo_entrada": "Hora_cal",
                                        "Toneladas": "Toneladas_h"})
        )

        bar_tons = (
            alt.Chart(tons_h)
            .mark_bar()
            .encode(x=alt.X("Hora_cal:T", title="Fecha-hora"),
                    y=alt.Y("Toneladas_h:Q", title="Toneladas"),
                    tooltip=["Hora_cal:T", "Toneladas_h"])
            .properties(height=300)
        )
        st.altair_chart(bar_tons, use_container_width=True)

    # ─── Expander con detalles ──────────────────────────────
    with st.expander("📍 Detalle de transiciones origen → destino"):
        st.dataframe(trans)

    # ─── Exportar a Excel ───────────────────────────────────
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
        trans.to_excel(xls, "Transiciones", index=False)
        viajes_h.to_excel(xls, "ViajesHora", index=False)
        ciclos.to_excel(xls, "Ciclos", index=False)
        productividad.to_excel(xls, "Productividad", index=False)
    st.download_button("💾 Descargar reporte Excel",
                       buf.getvalue(),
                       "reporte_operacional.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
