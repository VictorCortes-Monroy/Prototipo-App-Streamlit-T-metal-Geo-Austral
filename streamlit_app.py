"""
Streamlit App Principal - T-Metal BI Operacional
Este archivo es el punto de entrada para Streamlit Cloud
"""

# Importar y ejecutar la aplicación principal
import streamlit as st
import sys
import os

# Asegurar que el directorio actual esté en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar la aplicación principal desde app6_mejorado
try:
    # Ejecutar el contenido de app6_mejorado.py
    exec(open('app6_mejorado.py').read())
except Exception as e:
    st.error(f"Error al cargar la aplicación: {str(e)}")
    st.info("Por favor, asegúrese de que el archivo app6_mejorado.py esté disponible.")