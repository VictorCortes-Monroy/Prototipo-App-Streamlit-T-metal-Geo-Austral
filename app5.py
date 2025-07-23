"""
Streamlit - T-Metal · BI Operacional
Versión 2025-06-25 – incluye:
• Producción horaria (viajes de carga y descarga)
• Conteo detallado de viajes por tipo (carga, descarga, retorno, otros)
• Ciclos completos por vehículo
• Productividad (% horas de carga vs horas activas)
• Toneladas acumuladas (≈ N(42 t, σ = 3 t) por viaje de producción)
• Soporte para Pilas ROM (Pila Rom 1, Pila Rom 2, Pila Rom 3)
• Filtros por turno (día/noche) con métricas diferenciadas
• Exportación a Excel
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import unicodedata
from datetime import time
from io import BytesIO

st.set_page_config(
    page_title="⛏️ T-Metal – BI Operacional",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    return df


def poblar_dominios(df: pd.DataFrame) -> None:
    """Detecta automáticamente STOCKS, MODULES, BOTADEROS, PILAS_ROM."""
    global STOCKS, MODULES, BOTADEROS, PILAS_ROM
    geos = set(df["Geocerca"].unique()) - {""}
    STOCKS    = {g for g in geos if "stock"    in normalizar(g)}
    MODULES   = {g for g in geos if "modulo"   in normalizar(g)}
    BOTADEROS = {g for g in geos if "botadero" in normalizar(g)} or {"Botaderos"}
    PILAS_ROM = {g for g in geos if "pila rom" in normalizar(g)}


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
# 4 | Detección de ciclos Stock→Módulo/Pila ROM→Stock
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
    if trans.empty:
        st.warning("No se encontraron transiciones válidas.")
        st.stop()

    trans["Proceso"] = trans.apply(clasificar_proceso, axis=1)
    ciclos           = detectar_ciclos(trans)
    viajes_h, productividad = construir_metricas(trans)

    # ────────────────────────────────────────────────────────
    #  Dashboard
    # ────────────────────────────────────────────────────────
    st.subheader("🔋 Producción horaria – Viajes de carga y descarga")
    
    # Crear gráfico combinado de carga y descarga
    if not trans.empty:
        # Preparar datos para el gráfico
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
    st.subheader("🌅🌙 Producción horaria por turno")
    
    # Crear datos por turno para gráficos
    if not trans.empty:
        # Agregar hora y turno a los datos de viajes (carga y descarga)
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
            
            # Resumen comparativo
            if not viajes_dia_hora.empty or not viajes_noche_hora.empty:
                st.markdown("**📊 Resumen comparativo**")
                resumen_data = {
                    "Turno": ["Día", "Noche"],
                    "Total Viajes": [
                        len(viajes_dia_hora) if not viajes_dia_hora.empty else 0,
                        len(viajes_noche_hora) if not viajes_noche_hora.empty else 0
                    ]
                }
                resumen_df = pd.DataFrame(resumen_data)
                st.dataframe(resumen_df, use_container_width=True)

    # Conteo global de viajes
    st.subheader("📊 Conteo global de viajes (período filtrado)")
    
    # Crear resumen más detallado
    if not trans.empty:
        # Contar por tipo de proceso
        conteo_procesos = trans["Proceso"].value_counts()
        
        # Crear DataFrame con información detallada
        resumen_viajes = pd.DataFrame({
            "Tipo de Viaje": ["Carga", "Descarga", "Retorno", "Otros"],
        })
        
        # Mapear nombres de procesos a nombres más amigables
        mapeo_procesos = {
            "carga": "Carga",
            "descarga": "Descarga", 
            "retorno": "Retorno",
            "otro": "Otros"
        }
        
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
        
        # Información adicional
        st.info(f"""
        **📈 Resumen de producción:**
        - **Total viajes de producción**: {conteo_procesos.get('carga', 0) + conteo_procesos.get('descarga', 0)} 
        (Carga + Descarga)
        - **Total viajes operacionales**: {total_viajes}
        - **Eficiencia**: {((conteo_procesos.get('carga', 0) + conteo_procesos.get('descarga', 0)) / total_viajes * 100):.1f}% de viajes son de producción
        """)
    else:
        st.info("Sin transiciones disponibles para mostrar conteo.")

    # ─── Métricas por turno ──────────────────────────────────────
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

    # Ciclos completos por vehículo
    st.subheader("🔄 Ciclos completos (Stock→Módulo/Pila ROM→Stock)")
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
    
    # Incluir tanto carga como descarga para estimación de toneladas
    viajes_produccion = trans[trans["Proceso"].isin(["carga", "descarga"])].copy()
    if viajes_produccion.empty:
        st.info("Sin viajes de producción (carga/descarga) – no se estiman toneladas.")
    else:
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

    # ─── Expander con detalles ──────────────────────────────
    with st.expander("📍 Detalle de transiciones origen → destino"):
        st.dataframe(trans)

    # ─── Exportar a Excel ───────────────────────────────────
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xls:
        trans.to_excel(excel_writer=xls, sheet_name="Transiciones", index=False)
        viajes_h.to_excel(excel_writer=xls, sheet_name="ViajesHora", index=False)
        ciclos.to_excel(excel_writer=xls, sheet_name="Ciclos", index=False)
        productividad.to_excel(excel_writer=xls, sheet_name="Productividad", index=False)
    st.download_button("💾 Descargar reporte Excel",
                       buf.getvalue(),
                       "reporte_operacional.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
