"""
Script de pruebas automatizadas para app5.py
Ejecuta pruebas unitarias de las funciones principales
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import sys
import os

# Agregar el directorio actual al path para importar funciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar funciones de app5.py
from app5 import (
    turno, normalizar, preparar_datos, poblar_dominios,
    extraer_transiciones, clasificar_proceso, detectar_ciclos,
    construir_metricas
)

def test_turno():
    """Prueba la función de clasificación de turnos"""
    print("🧪 Probando función turno()...")
    
    # Casos de prueba
    test_cases = [
        (datetime(2025, 1, 15, 8, 0), "dia"),    # 8:00 AM
        (datetime(2025, 1, 15, 12, 0), "dia"),   # 12:00 PM
        (datetime(2025, 1, 15, 19, 59), "dia"),  # 7:59 PM
        (datetime(2025, 1, 15, 20, 0), "noche"), # 8:00 PM
        (datetime(2025, 1, 15, 23, 0), "noche"), # 11:00 PM
        (datetime(2025, 1, 15, 2, 0), "noche"),  # 2:00 AM
        (datetime(2025, 1, 15, 7, 59), "noche"), # 7:59 AM
    ]
    
    for timestamp, expected in test_cases:
        result = turno(timestamp)
        assert result == expected, f"Error: {timestamp} -> {result}, esperado: {expected}"
    
    print("✅ Función turno() - OK")

def test_normalizar():
    """Prueba la función de normalización de texto"""
    print("🧪 Probando función normalizar()...")
    
    test_cases = [
        ("Pila Rom 1", "pila rom 1"),
        ("MÓDULO 2", "modulo 2"),
        ("Stock Principal", "stock principal"),
        ("Botadero Central", "botadero central"),
    ]
    
    for input_text, expected in test_cases:
        result = normalizar(input_text)
        assert result == expected, f"Error: '{input_text}' -> '{result}', esperado: '{expected}'"
    
    print("✅ Función normalizar() - OK")

def test_preparar_datos():
    """Prueba la preparación de datos"""
    print("🧪 Probando función preparar_datos()...")
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        "Nombre del Vehículo": ["Camión_001", "Camión_001", "Camión_002"],
        "Tiempo de evento": ["2025-01-15 08:30:00", "2025-01-15 08:45:00", "2025-01-15 20:30:00"],
        "Geocercas": ["Stock Principal", "Módulo 1", "Stock Secundario"]
    })
    
    result = preparar_datos(test_data)
    
    # Verificaciones
    assert len(result) == 3, f"Error: Se esperaban 3 filas, se obtuvieron {len(result)}"
    assert "Tiempo de evento" in result.columns, "Error: Columna 'Tiempo de evento' no encontrada"
    assert "Geocerca" in result.columns, "Error: Columna 'Geocerca' no encontrada"
    assert result["Tiempo de evento"].dtype == "datetime64[ns]", "Error: Tipo de dato incorrecto para tiempo"
    
    print("✅ Función preparar_datos() - OK")

def test_poblar_dominios():
    """Prueba la detección de dominios"""
    print("🧪 Probando función poblar_dominios()...")
    
    # Crear datos con diferentes tipos de geocercas
    test_data = pd.DataFrame({
        "Geocerca": [
            "Stock Principal", "Stock Secundario",
            "Módulo 1", "Módulo 2", "Módulo 3",
            "Pila Rom 1", "Pila Rom 2", "Pila Rom 3",
            "Botadero Central", "Botadero Norte"
        ]
    })
    
    poblar_dominios(test_data)
    
    # Verificar que se detectaron correctamente
    from app5 import STOCKS, MODULES, PILAS_ROM, BOTADEROS
    
    assert len(STOCKS) >= 2, f"Error: Se esperaban al menos 2 stocks, se encontraron {len(STOCKS)}"
    assert len(MODULES) >= 3, f"Error: Se esperaban al menos 3 módulos, se encontraron {len(MODULES)}"
    assert len(PILAS_ROM) >= 3, f"Error: Se esperaban al menos 3 pilas ROM, se encontraron {len(PILAS_ROM)}"
    assert len(BOTADEROS) >= 2, f"Error: Se esperaban al menos 2 botaderos, se encontraron {len(BOTADEROS)}"
    
    print("✅ Función poblar_dominios() - OK")

def test_clasificar_proceso():
    """Prueba la clasificación de procesos"""
    print("🧪 Probando función clasificar_proceso()...")
    
    # Configurar dominios primero
    test_data = pd.DataFrame({
        "Geocerca": ["Stock Principal", "Módulo 1", "Pila Rom 1", "Botadero Central"]
    })
    poblar_dominios(test_data)
    
    # Casos de prueba
    test_cases = [
        ({"Origen": "Stock Principal", "Destino": "Módulo 1"}, "carga"),
        ({"Origen": "Stock Principal", "Destino": "Pila Rom 1"}, "carga"),
        ({"Origen": "Módulo 1", "Destino": "Stock Principal"}, "retorno"),
        ({"Origen": "Pila Rom 1", "Destino": "Stock Principal"}, "retorno"),
        ({"Origen": "Módulo 1", "Destino": "Botadero Central"}, "descarga"),
        ({"Origen": "Pila Rom 1", "Destino": "Botadero Central"}, "descarga"),
        ({"Origen": "Stock Principal", "Destino": "Botadero Central"}, "otro"),
    ]
    
    for input_data, expected in test_cases:
        result = clasificar_proceso(pd.Series(input_data))
        assert result == expected, f"Error: {input_data} -> {result}, esperado: {expected}"
    
    print("✅ Función clasificar_proceso() - OK")

def test_extraer_transiciones():
    """Prueba la extracción de transiciones"""
    print("🧪 Probando función extraer_transiciones()...")
    
    # Crear datos de prueba con transiciones válidas
    test_data = pd.DataFrame({
        "Nombre del Vehículo": ["Camión_001", "Camión_001", "Camión_001"],
        "Tiempo de evento": [
            pd.Timestamp("2025-01-15 08:30:00"),
            pd.Timestamp("2025-01-15 08:45:00"),
            pd.Timestamp("2025-01-15 09:15:00")
        ],
        "Geocerca": ["Stock Principal", "Módulo 1", "Stock Principal"]
    })
    
    result = extraer_transiciones(test_data)
    
    # Verificaciones básicas
    assert isinstance(result, pd.DataFrame), "Error: El resultado debe ser un DataFrame"
    assert "Origen" in result.columns, "Error: Columna 'Origen' no encontrada"
    assert "Destino" in result.columns, "Error: Columna 'Destino' no encontrada"
    assert "Duracion_s" in result.columns, "Error: Columna 'Duracion_s' no encontrada"
    
    print("✅ Función extraer_transiciones() - OK")

def test_detectar_ciclos():
    """Prueba la detección de ciclos"""
    print("🧪 Probando función detectar_ciclos()...")
    
    # Crear transiciones de prueba
    test_trans = pd.DataFrame({
        "Nombre del Vehículo": ["Camión_001", "Camión_001"],
        "Origen": ["Stock Principal", "Módulo 1"],
        "Destino": ["Módulo 1", "Stock Principal"],
        "Tiempo_entrada": [
            pd.Timestamp("2025-01-15 08:30:00"),
            pd.Timestamp("2025-01-15 08:45:00")
        ],
        "Tiempo_salida": [
            pd.Timestamp("2025-01-15 08:45:00"),
            pd.Timestamp("2025-01-15 09:15:00")
        ],
        "Duracion_s": [900, 1800],
        "Turno": ["dia", "dia"]
    })
    
    result = detectar_ciclos(test_trans)
    
    # Verificaciones
    assert isinstance(result, pd.DataFrame), "Error: El resultado debe ser un DataFrame"
    
    print("✅ Función detectar_ciclos() - OK")

def test_construir_metricas():
    """Prueba la construcción de métricas"""
    print("🧪 Probando función construir_metricas()...")
    
    # Crear transiciones de prueba
    test_trans = pd.DataFrame({
        "Nombre del Vehículo": ["Camión_001", "Camión_001", "Camión_002"],
        "Origen": ["Stock Principal", "Módulo 1", "Stock Secundario"],
        "Destino": ["Módulo 1", "Stock Principal", "Módulo 2"],
        "Tiempo_entrada": [
            pd.Timestamp("2025-01-15 08:30:00"),
            pd.Timestamp("2025-01-15 08:45:00"),
            pd.Timestamp("2025-01-15 20:30:00")
        ],
        "Tiempo_salida": [
            pd.Timestamp("2025-01-15 08:45:00"),
            pd.Timestamp("2025-01-15 09:15:00"),
            pd.Timestamp("2025-01-15 20:45:00")
        ],
        "Duracion_s": [900, 1800, 900],
        "Turno": ["dia", "dia", "noche"]
    })
    
    viajes_h, productividad = construir_metricas(test_trans)
    
    # Verificaciones
    assert isinstance(viajes_h, pd.DataFrame), "Error: viajes_h debe ser un DataFrame"
    assert isinstance(productividad, pd.DataFrame), "Error: productividad debe ser un DataFrame"
    
    print("✅ Función construir_metricas() - OK")

def test_datos_completos():
    """Prueba con datos completos del archivo CSV"""
    print("🧪 Probando con datos completos del CSV...")
    
    try:
        # Cargar datos de prueba
        df_raw = pd.read_csv("datos_prueba.csv")
        df = preparar_datos(df_raw)
        
        # Verificar que se cargaron correctamente
        assert len(df) > 0, "Error: No se cargaron datos del CSV"
        assert "Nombre del Vehículo" in df.columns, "Error: Columna de vehículo no encontrada"
        assert "Tiempo de evento" in df.columns, "Error: Columna de tiempo no encontrada"
        assert "Geocerca" in df.columns, "Error: Columna de geocerca no encontrada"
        
        # Poblar dominios
        poblar_dominios(df)
        
        # Extraer transiciones
        trans = extraer_transiciones(df)
        assert len(trans) > 0, "Error: No se extrajeron transiciones"
        
        # Clasificar procesos
        trans["Proceso"] = trans.apply(clasificar_proceso, axis=1)
        
        # Verificar que se clasificaron correctamente
        procesos_unicos = trans["Proceso"].unique()
        assert "carga" in procesos_unicos, "Error: No se detectaron procesos de carga"
        assert "retorno" in procesos_unicos, "Error: No se detectaron procesos de retorno"
        assert "descarga" in procesos_unicos, "Error: No se detectaron procesos de descarga"
        
        # Detectar ciclos
        ciclos = detectar_ciclos(trans)
        
        # Construir métricas
        viajes_h, productividad = construir_metricas(trans)
        
        print(f"✅ Datos completos - OK")
        print(f"   - Transiciones: {len(trans)}")
        print(f"   - Ciclos: {len(ciclos)}")
        print(f"   - Viajes por hora: {len(viajes_h)}")
        print(f"   - Registros de productividad: {len(productividad)}")
        
    except Exception as e:
        print(f"❌ Error en prueba de datos completos: {e}")
        raise

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas automatizadas para app5.py")
    print("=" * 50)
    
    try:
        test_turno()
        test_normalizar()
        test_preparar_datos()
        test_poblar_dominios()
        test_clasificar_proceso()
        test_extraer_transiciones()
        test_detectar_ciclos()
        test_construir_metricas()
        test_datos_completos()
        
        print("=" * 50)
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ La aplicación está lista para producción")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Error en las pruebas: {e}")
        print("🔧 Revisa el código antes de continuar")
        return False
    
    return True

if __name__ == "__main__":
    main() 