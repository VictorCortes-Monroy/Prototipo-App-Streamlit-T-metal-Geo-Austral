# 📊 **DOCUMENTACIÓN TÉCNICA - T-Metal BI Operacional v6.0**

## 🎯 **Descripción General**

**`app6_mejorado.py`** es la aplicación principal de análisis operacional de T-Metal, diseñada para proporcionar insights completos sobre la operación minera, incluyendo análisis de productividad, detección de anomalías, y optimización de procesos.

### **🏭 Propósito Operacional**
- **Análisis de Productividad**: Métricas detalladas de carga/descarga por turno
- **Detección de Anomalías**: Identificación automática de detenciones anómalas
- **Optimización de Rutas**: Análisis de zonas no mapeadas y eficiencia
- **Gestión de Flota**: Seguimiento completo de vehículos y geocercas

---

## 🏗️ **Arquitectura del Sistema**

### **📋 Componentes Principales**

#### **1. Sistema de Normalización Inteligente**
```python
def normalizar_geocerca(geocerca_original: str) -> str:
    """
    Sistema avanzado de normalización que maneja:
    - Múltiples geocercas en una celda (separadas por ';')
    - Unificación de variantes (stock central = Stock Central - 30 km hr)
    - Exclusión de rutas (Ruta*, Camino* → "")
    - Priorización inteligente de geocercas operacionales
    """
```

#### **2. Clasificación de Procesos Operacionales**
```python
def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica cada transición en:
    - "carga": Movimiento hacia stocks/modules
    - "descarga": Movimiento desde stocks/modules
    - "otro": Movimientos no productivos
    - "retorno": Retorno a base
    """
```

#### **3. Detección de Anomalías Avanzada**
```python
def analizar_detenciones_anomalas(df: pd.DataFrame, trans: pd.DataFrame) -> pd.DataFrame:
    """
    Sistema ML para detectar detenciones anómalas:
    - Velocidad < 2 km/h por > 10 minutos
    - Duración > promedio + 2σ por geocerca
    - Clasificación por severidad (Alta/Media)
    - Alertas automáticas para mantenimiento
    """
```

---

## 🔧 **Funcionalidades Específicas**

### **📊 Análisis de Productividad**

#### **Métricas por Turno**
- **Carga/Descarga por Hora**: Análisis detallado de productividad
- **Toneladas Acumuladas**: Estimaciones basadas en patrones históricos
- **Eficiencia Operacional**: Comparación día vs noche

#### **Matriz de Viajes**
- **Origen → Destino**: Visualización completa de flujos
- **Filtros Dinámicos**: Por geocerca, vehículo, fecha
- **Métricas Agregadas**: Totales y promedios por ruta

### **🚨 Sistema de Detección de Anomalías**

#### **Criterios de Detección**
```python
# Supuestos establecidos:
# 1. Detención = velocidad < 2 km/h por más de 10 minutos consecutivos
# 2. Anómala = duración > promedio + 2σ de la geocerca específica
# 3. Solo se analizan geocercas operacionales (stocks, modules, pilas_rom, botaderos)
# 4. Se excluyen detenciones normales de carga/descarga (< 30 min)
```

#### **Clasificación por Severidad**
- **🔴 Alta**: > 3σ del promedio (requiere atención inmediata)
- **🟡 Media**: 2-3σ del promedio (monitoreo recomendado)

### **🗺️ Análisis de Zonas No Mapeadas**

#### **Algoritmo DBSCAN**
```python
def analizar_zonas_no_mapeadas(df: pd.DataFrame, 
                              velocidad_max: float = 5.0,
                              tiempo_min_minutos: int = 10,
                              radio_agrupacion: float = 10.0) -> pd.DataFrame:
    """
    Identifica zonas de actividad no registradas:
    - Clustering geográfico de puntos de baja velocidad
    - Filtrado por tiempo mínimo de estancia
    - Agrupación por proximidad espacial
    """
```

---

## 📈 **Métricas y KPIs**

### **🎯 Indicadores de Productividad**
- **Viajes por Hora**: Tasa de movimientos productivos
- **Tiempo Promedio de Viaje**: Eficiencia de rutas
- **Utilización de Flota**: Porcentaje de tiempo activo
- **Productividad por Turno**: Comparación día/noche

### **🚨 Indicadores de Anomalías**
- **Detenciones Anómalas**: Cantidad y severidad
- **Tiempo Perdido**: Impacto en productividad
- **Patrones Recurrentes**: Identificación de problemas sistémicos

### **🗺️ Indicadores Geográficos**
- **Zonas No Mapeadas**: Áreas de actividad no registrada
- **Eficiencia de Rutas**: Optimización de trayectos
- **Cobertura de Geocercas**: Completitud del mapeo

---

## 🔄 **Flujo de Procesamiento de Datos**

### **1. Preparación de Datos**
```python
def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    # Conversión de timestamps
    # Normalización de geocercas
    # Ordenamiento por vehículo y tiempo
```

### **2. Normalización Inteligente**
```python
def normalizar_geocerca(geocerca_original: str) -> str:
    # Manejo de múltiples geocercas
    # Unificación de variantes
    # Exclusión de rutas
    # Priorización operacional
```

### **3. Clasificación de Procesos**
```python
def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    # Identificación de orígenes/destinos
    # Clasificación por tipo de proceso
    # Cálculo de métricas por transición
```

### **4. Análisis de Anomalías**
```python
def analizar_detenciones_anomalas(df: pd.DataFrame, trans: pd.DataFrame) -> pd.DataFrame:
    # Segmentación por vehículo y geocerca
    # Cálculo de umbrales estadísticos
    # Clasificación por severidad
    # Generación de alertas
```

---

## 🎨 **Interfaz de Usuario**

### **📊 Dashboard Principal**
- **Filtros Avanzados**: Por geocerca, vehículo, fecha, turno
- **Métricas en Tiempo Real**: KPIs actualizados dinámicamente
- **Visualizaciones Interactivas**: Gráficos y mapas responsivos

### **🚨 Panel de Anomalías**
- **Alertas Prioritarias**: Detenciones de alta severidad
- **Análisis Detallado**: Tablas con información completa
- **Visualizaciones Temporales**: Líneas de tiempo de eventos

### **🗺️ Mapa de Calor**
- **Zonas de Actividad**: Visualización geográfica
- **Clusters de Anomalías**: Agrupación espacial
- **Interactividad**: Zoom y filtros dinámicos

---

## ⚡ **Performance y Optimización**

### **🚀 Optimizaciones Implementadas**
- **Procesamiento Vectorizado**: Uso intensivo de pandas/numpy
- **Caching Inteligente**: Reutilización de cálculos
- **Filtrado Eficiente**: Reducción de datos innecesarios
- **Visualizaciones Optimizadas**: Renderizado condicional

### **📊 Métricas de Performance**
- **Tiempo de Carga**: < 5 segundos para datasets típicos
- **Uso de Memoria**: Optimizado para archivos grandes
- **Responsividad**: Interfaz fluida en tiempo real

---

## 🔧 **Configuración y Personalización**

### **⚙️ Parámetros Globales**
```python
MIN_ESTANCIA_S      = 3  # Tiempo mínimo de estancia
SHIFT_DAY_START     = time(8, 0)   # Inicio turno día
SHIFT_NIGHT_START   = time(20, 0)  # Inicio turno noche
```

### **🎯 Umbrales de Anomalías**
```python
VELOCIDAD_DETENCION = 2.0  # km/h para considerar detención
TIEMPO_MIN_DETENCION = 10  # minutos mínimos
MULTIPLO_ANOMALO = 2.0     # σ para clasificar como anómala
```

---

## 🚀 **Casos de Uso Operacional**

### **👷‍♂️ Para Supervisores de Operaciones**
- **Monitoreo en Tiempo Real**: Estado actual de la flota
- **Detección de Problemas**: Alertas automáticas de anomalías
- **Optimización de Turnos**: Análisis de productividad por turno

### **🔧 Para Mantenimiento**
- **Detección de Fallas**: Patrones de detenciones anómalas
- **Planificación Preventiva**: Identificación de problemas recurrentes
- **Optimización de Rutas**: Análisis de zonas no mapeadas

### **📊 Para Gestión**
- **Reportes de Productividad**: Métricas agregadas por período
- **Análisis de Eficiencia**: Comparación de rendimientos
- **Toma de Decisiones**: Datos para optimización operacional

---

## 🔮 **Roadmap y Mejoras Futuras**

### **🎯 Próximas Funcionalidades**
- **Predicción de Fallas**: ML para anticipar problemas
- **Optimización Automática**: Sugerencias de rutas
- **Integración IoT**: Datos en tiempo real de sensores
- **Alertas Push**: Notificaciones automáticas

### **📈 Escalabilidad**
- **Big Data**: Procesamiento de datasets masivos
- **Cloud Native**: Despliegue en la nube
- **API REST**: Integración con otros sistemas
- **Microservicios**: Arquitectura distribuida

---

## 📚 **Referencias Técnicas**

### **🔧 Librerías Utilizadas**
- **Streamlit**: Framework web para dashboards
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Computación numérica
- **Altair**: Visualizaciones estadísticas
- **Folium**: Mapas interactivos
- **Scikit-learn**: Machine Learning (DBSCAN)

### **📖 Algoritmos Implementados**
- **DBSCAN**: Clustering espacial para zonas no mapeadas
- **Análisis Estadístico**: Detección de anomalías
- **Normalización de Texto**: Procesamiento de geocercas
- **Cálculo de Distancias**: Fórmula de Haversine

---

## 📋 **Documentación Relacionada**

### **📚 Guías de Usuario**
- **`GUIA_USUARIO_APP6_MEJORADO.md`**: Guía completa para usuarios de esta aplicación
- **`GUIA_USUARIO_APP7TPORT.md`**: Guía para la aplicación de secuencias de viajes

### **📖 Documentación Técnica**
- **`DOCUMENTACION_APP7TPORT.md`**: Documentación técnica de la aplicación de secuencias
- **`GUIA_DESPLIEGUE_STREAMLIT.md`**: Guía de despliegue en Streamlit Cloud

### **🔧 Funcionalidades Específicas**
- **`NUEVAS_FUNCIONALIDADES_V6.md`**: Detalles de las nuevas funcionalidades implementadas

---

## 🎯 **Comparación con app7tport.py**

| Aspecto | app6_mejorado.py | app7tport.py |
|---------|------------------|---------------|
| **Enfoque** | Análisis operacional completo | Secuencias de viajes específicas |
| **Geocercas** | Todas las geocercas detectadas | Solo geocercas específicas predefinidas |
| **Métricas** | Productividad, anomalías, toneladas | Secuencias, patrones, frecuencias |
| **Complejidad** | Alta (múltiples funcionalidades) | Media (enfoque simplificado) |
| **Casos de Uso** | Supervisores, mantenimiento, gestión | Transporte, planificación operacional |
| **Anomalías** | Detección avanzada de detenciones | No incluye análisis de anomalías |
| **Consolidación** | No aplica | Consolidación de estadías internas |

**Elige según tu necesidad**:
- **app6_mejorado.py**: Para análisis operacional completo con detección de anomalías
- **app7tport.py**: Para análisis especializado de secuencias de viajes

---

## 🎉 **Conclusión**

**`app6_mejorado.py`** representa la evolución completa del sistema de análisis operacional de T-Metal, combinando análisis tradicional de productividad con tecnologías avanzadas de detección de anomalías y optimización operacional. Su arquitectura modular y funcionalidades avanzadas lo convierten en una herramienta esencial para la toma de decisiones operacionales.

**Para análisis especializado de secuencias de viajes**, consulta la documentación de **`app7tport.py`** que proporciona funcionalidades específicas para visualización de patrones de movimiento entre geocercas predefinidas.

---

*Última actualización: Enero 2025*  
*Versión: 6.0 Mejorado*  
*Documentación específica para análisis operacional completo*