import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import unicodedata
from datetime import time
from io import BytesIO

st.set_page_config(page_title="⛏️ T-Metal – BI Operacional", layout="wide")

# -------- parámetros ----------
MIN_ESTANCIA_S      = 60
SHIFT_DAY_START     = time(8, 0)
SHIFT_NIGHT_START   = time(20, 0)

# -------- utilidades ----------
norm = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

def turno(ts):  # día / noche
    h = ts.time()
    return "dia" if SHIFT_DAY_START <= h < SHIFT_NIGHT_START else "noche"

def preparar_datos(df):
    df = df.copy()
    df["Tiempo de evento"] = pd.to_datetime(df["Tiempo de evento"], errors="coerce")
    df.dropna(subset=["Tiempo de evento"], inplace=True)
    df["Geocerca"] = df["Geocercas"].fillna("").str.strip()
    df.sort_values(["Nombre del Vehículo", "Tiempo de evento"], inplace=True)
    return df

def poblar_dominios(df):
    geos       = set(df["Geocerca"].unique()) - {""}
    stocks     = {g for g in geos if "stock"    in norm(g)}
    modules    = {g for g in geos if "modulo"   in norm(g)}
    botaderos  = {g for g in geos if "botadero" in norm(g)} or {"Botaderos"}
    return stocks, modules, botaderos

def extraer_transiciones(df):
    regs = []
    for veh, g in df.groupby("Nombre del Vehículo"):
        g = g[g["Geocerca"] != ""].copy()
        if g.empty:
            continue
        g["Geo_next"]  = g["Geocerca"].shift(-1)
        g["Time_next"] = g["Tiempo de evento"].shift(-1)
        c = g[g["Geo_next"].notna() & (g["Geocerca"] != g["Geo_next"])].copy()
        c["Duracion_s"] = (c["Time_next"] - c["Tiempo de evento"]).dt.total_seconds()
        c = c[c["Duracion_s"] >= MIN_ESTANCIA_S]
        if c.empty:
            continue
        c["Origen"]  = c["Geocerca"]
        c["Destino"] = c["Geo_next"]
        c["Tiempo_entrada"] = c["Tiempo de evento"]
        c["Tiempo_salida"]  = c["Time_next"]
        c["Turno"]          = c["Tiempo_entrada"].apply(turno)
        regs.append(c[["Nombre del Vehículo","Origen","Destino",
                       "Tiempo_entrada","Tiempo_salida","Duracion_s","Turno"]])
    return pd.concat(regs, ignore_index=True) if regs else pd.DataFrame(columns=[
        "Nombre del Vehículo","Origen","Destino","Tiempo_entrada","Tiempo_salida",
        "Duracion_s","Turno"])

def clasificar_proceso(row, stocks, modules, botaderos):
    o, d = row["Origen"], row["Destino"]
    if o in stocks   and d in modules:   return "carga"
    if o in modules  and d in stocks:    return "retorno"
    if o in modules  and d in botaderos: return "descarga"
    return "otro"

def detectar_ciclos(t):
    t = t.sort_values(["Nombre del Vehículo","Tiempo_entrada"]).copy()
    t["Proc_next"] = t.groupby("Nombre del Vehículo")["Proceso"].shift(-1)
    mask = (t["Proceso"] == "carga") & (t["Proc_next"] == "retorno")
    res  = t[mask].copy()
    res["Ciclo_ID"] = np.arange(len(res))
    return res

def construir_metricas(trans):
    if trans.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    trans["Hora_cal"] = trans["Tiempo_entrada"].dt.floor("h")
    v_h = (trans.groupby(["Hora_cal","Proceso"])
                 .size().unstack(fill_value=0).reset_index())
    v_h = v_h.reindex(columns=["Hora_cal","carga","retorno","descarga","otro"],
                      fill_value=0)
    trans["Duracion_h"] = trans["Duracion_s"]/3600
    act = (trans.groupby([trans["Tiempo_entrada"].dt.date.rename("Fecha"),
                          "Nombre del Vehículo"])
                 ["Duracion_h"].sum().reset_index())
    return v_h, act

# -------- UI ----------
st.header("📤 Cargar CSV de eventos GPS")
file = st.file_uploader("Selecciona el CSV exportado desde GeoAustral", type=["csv"])

if file:
    raw = pd.read_csv(file)
    df  = preparar_datos(raw)
    STOCKS, MODULES, BOTADEROS = poblar_dominios(df)

    # filtros
    dmin, dmax = df["Tiempo de evento"].min().date(), df["Tiempo de evento"].max().date()
    r = st.date_input("Rango de fechas", [dmin,dmax])
    if isinstance(r, tuple) and len(r)==1: r = (r[0], r[0])
    df = df[(df["Tiempo de evento"].dt.date >= r[0]) & (df["Tiempo de evento"].dt.date <= r[1])]

    veh_opts = ["Todos"] + sorted(df["Nombre del Vehículo"].unique())
    veh_sel  = st.selectbox("Vehículo", veh_opts)
    if veh_sel != "Todos":
        df = df[df["Nombre del Vehículo"] == veh_sel]

    trans = extraer_transiciones(df)
    if not trans.empty:
        trans["Proceso"] = trans.apply(clasificar_proceso, axis=1,
                                       args=(STOCKS, MODULES, BOTADEROS))
        ciclos = detectar_ciclos(trans)
        viajes_h, actividad = construir_metricas(trans)

        # --- dashboard ---
        st.subheader("🔋 Producción horaria – viajes de carga")
        carga_h = viajes_h[["Hora_cal","carga"]].rename(columns={"carga":"Viajes_de_carga"})
        chart = (alt.Chart(carga_h)
                 .mark_line(point=True)
                 .encode(x="Hora_cal:T", y="Viajes_de_carga:Q",
                         tooltip=["Hora_cal","Viajes_de_carga"])
                 .properties(height=300))
        st.altair_chart(chart, use_container_width=True)

        st.subheader("📊 Conteo de viajes por tipo")
        st.dataframe(viajes_h.set_index("Hora_cal").sum().astype(int).to_frame("Total"))

        st.subheader("🔄 Ciclos completos por vehículo")
        ciclos_por_veh = (ciclos.groupby("Nombre del Vehículo")
                                   .size().reset_index(name="Ciclos")
                                   .sort_values("Ciclos", ascending=False))
        st.dataframe(ciclos_por_veh)

        with st.expander("Detalles origen → destino"):
            st.dataframe(trans)

        # --- exportar excel ---
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
            trans.to_excel(xls, "Transiciones", index=False)
            viajes_h.to_excel(xls, "ViajesHora", index=False)
            ciclos.to_excel(xls, "Ciclos", index=False)
            actividad.to_excel(xls, "Actividad", index=False)
        st.download_button("💾 Descargar reporte Excel", buf.getvalue(),
                           "reporte_operacional.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
