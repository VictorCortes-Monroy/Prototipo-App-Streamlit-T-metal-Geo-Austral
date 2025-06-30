import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🛰️ Monitoreo de Vehículos por GPS")

# 1. Subir archivo CSV
archivo = st.file_uploader("📤 Sube tu archivo CSV de eventos GPS", type=["csv"])

if archivo is not None:
    df = pd.read_csv(archivo)

    # Conversión de columnas clave
    df['Tiempo de evento'] = pd.to_datetime(df['Tiempo de evento'], errors='coerce')
    df['Geocerca_estado'] = df['Geocercas'].fillna('En tránsito')
    df = df.sort_values(by=['Nombre del Vehículo', 'Tiempo de evento'])

    # Filtro por fecha
    fecha_min = df['Tiempo de evento'].min()
    fecha_max = df['Tiempo de evento'].max()
    rango_fecha = st.date_input("🕒 Rango de fechas", [fecha_min.date(), fecha_max.date()])
    df = df[(df['Tiempo de evento'].dt.date >= rango_fecha[0]) & (df['Tiempo de evento'].dt.date <= rango_fecha[1])]

    # Selección de vehículo o todos
    vehiculos = df['Nombre del Vehículo'].unique()
    vehiculo_seleccionado = st.selectbox("🚚 Selecciona un vehículo", options=["Todos los vehículos"] + list(vehiculos))

    if vehiculo_seleccionado == "Todos los vehículos":
        estadias_totales = []
        vueltas_totales = []
        resumenes = []

        for vehiculo in vehiculos:
            sub_df = df[df['Nombre del Vehículo'] == vehiculo].copy()
            sub_df = sub_df[sub_df['Geocerca_estado'] != 'En tránsito']
            sub_df['cambio'] = sub_df['Geocerca_estado'] != sub_df['Geocerca_estado'].shift()
            sub_df = sub_df[sub_df['cambio']]
            sub_df['Geocerca_anterior'] = sub_df['Geocerca_estado'].shift()
            sub_df['Tiempo_entrada'] = sub_df['Tiempo de evento']
            sub_df['Tiempo_salida'] = sub_df['Tiempo_entrada'].shift(-1)
            sub_df['Duración_horas'] = (sub_df['Tiempo_salida'] - sub_df['Tiempo_entrada']).dt.total_seconds() / 3600
            estadias = sub_df.dropna(subset=['Geocerca_anterior']).copy()
            estadias['Vehiculo'] = vehiculo
            estadias_totales.append(estadias[['Vehiculo', 'Geocerca_anterior', 'Tiempo_entrada', 'Tiempo_salida', 'Duración_horas']])

            vueltas = estadias[['Geocerca_anterior', 'Geocerca_estado']].copy()
            vueltas.columns = ['Origen', 'Destino']
            vueltas = vueltas.groupby(['Origen', 'Destino']).size().reset_index(name='Vueltas')
            vueltas['Vehiculo'] = vehiculo
            vueltas_totales.append(vueltas)

            zonas = estadias['Geocerca_anterior'].unique()
            total_horas = estadias['Duración_horas'].sum()
            resumen = f"🚚 Vehículo {vehiculo}:\n"
            resumen += f"- Estuvo activo en {len(zonas)} zonas distintas: {', '.join(zonas)}.\n"
            resumen += f"- Tiempo total registrado en geocercas: {total_horas:.1f} horas.\n"
            if not vueltas.empty:
                resumen += "- Vueltas detectadas:\n"
                for _, row in vueltas.iterrows():
                    resumen += f"    • {int(row['Vueltas'])} vueltas desde {row['Origen']} a {row['Destino']}\n"
            else:
                resumen += "- No se detectaron trayectos completos.\n"
            resumenes.append({'Vehiculo': vehiculo, 'Resumen': resumen})

        estadias_df = pd.concat(estadias_totales).reset_index(drop=True)
        vueltas_df = pd.concat(vueltas_totales).reset_index(drop=True)
        resumenes_df = pd.DataFrame(resumenes)

        st.subheader("📍 Estadías consolidadas")
        st.dataframe(estadias_df)

        st.subheader("🔁 Vueltas consolidadas")
        st.dataframe(vueltas_df)

        st.subheader("🧠 Resúmenes narrativos")
        st.dataframe(resumenes_df)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            estadias_df.to_excel(writer, sheet_name="Estadias", index=False)
            vueltas_df.to_excel(writer, sheet_name="Vueltas", index=False)
            resumenes_df.to_excel(writer, sheet_name="Resumen", index=False)

        st.download_button(
            label="📥 Descargar reporte Excel de todos los vehículos",
            data=buffer.getvalue(),
            file_name="reporte_todos_vehiculos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        df_v = df[df['Nombre del Vehículo'] == vehiculo_seleccionado].copy()

        # Estadías
        estadias = df_v[df_v['Geocerca_estado'] != 'En tránsito'].copy()
        estadias['cambio'] = estadias['Geocerca_estado'] != estadias['Geocerca_estado'].shift()
        estadias = estadias[estadias['cambio']]
        estadias['Geocerca_anterior'] = estadias['Geocerca_estado'].shift()
        estadias['Tiempo_entrada'] = estadias['Tiempo de evento']
        estadias['Tiempo_salida'] = estadias['Tiempo_entrada'].shift(-1)
        estadias['Duración_horas'] = (estadias['Tiempo_salida'] - estadias['Tiempo_entrada']).dt.total_seconds() / 3600
        estadias = estadias.dropna(subset=['Geocerca_anterior'])

        st.subheader("📍 Estadías del vehículo")
        st.dataframe(estadias[['Geocerca_anterior', 'Tiempo_entrada', 'Tiempo_salida', 'Duración_horas']])

        # Vueltas
        vueltas = estadias[['Geocerca_anterior', 'Geocerca_estado']]
        vueltas.columns = ['Origen', 'Destino']
        vueltas = vueltas.groupby(['Origen', 'Destino']).size().reset_index(name='Vueltas')

        st.subheader("🔁 Vueltas detectadas")
        st.dataframe(vueltas)

        # Mapa
        st.subheader("🗺️ Mapa del recorrido GPS")
        if df_v[['Latitud', 'Longitud']].dropna().shape[0] > 0:
            centro = [df_v['Latitud'].mean(), df_v['Longitud'].mean()]
            m = folium.Map(location=centro, zoom_start=12)
            cluster = MarkerCluster().add_to(m)

            for _, row in df_v.dropna(subset=['Latitud', 'Longitud']).iterrows():
                folium.Marker(
                    location=[row['Latitud'], row['Longitud']],
                    popup=row['Tiempo de evento'].strftime("%Y-%m-%d %H:%M:%S")
                ).add_to(cluster)

            st_folium(m, width=1000)
        else:
            st.warning("Este vehículo no tiene coordenadas válidas para mostrar.")

        # Resumen narrativo
        zonas = estadias['Geocerca_anterior'].unique()
        total_horas = estadias['Duración_horas'].sum()
        resumen = f"🚚 Vehículo {vehiculo_seleccionado} estuvo activo en {len(zonas)} zonas distintas: {', '.join(zonas)}.\n"
        resumen += f"Tiempo total registrado en geocercas: {total_horas:.1f} horas.\n"
        if not vueltas.empty:
            resumen += "Vueltas detectadas:\n"
            for _, row in vueltas.iterrows():
                resumen += f"• {int(row['Vueltas'])} vueltas desde {row['Origen']} a {row['Destino']}\n"
        else:
            resumen += "No se detectaron trayectos completos."

        st.subheader("🧠 Resumen narrativo del vehículo")
        st.text(resumen)

        # Descargar reporte en Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            estadias.to_excel(writer, sheet_name="Estadias", index=False)
            vueltas.to_excel(writer, sheet_name="Vueltas", index=False)
            pd.DataFrame([{'Resumen': resumen}]).to_excel(writer, sheet_name="Resumen", index=False)

        st.download_button(
            label="📥 Descargar reporte Excel",
            data=buffer.getvalue(),
            file_name=f"reporte_{vehiculo_seleccionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
