# 🚛 **DOCUMENTACIÓN TÉCNICA - T-Metal Análisis de Secuencias de Viajes v7.0**

## 🎯 **Descripción General**

**`app7tport.py`** es una aplicación especializada en análisis de secuencias de viajes entre geocercas específicas, diseñada para proporcionar una visualización clara y simplificada de los patrones de movimiento de la flota minera, eliminando la complejidad de métricas operacionales tradicionales.

### **🚛 Propósito Específico**
- **Análisis de Secuencias**: Visualización de patrones de movimiento entre geocercas específicas
- **Consolidación de Estadías**: Agrupación inteligente de transiciones internas
- **Simplificación Operacional**: Enfoque en secuencias origen-destino
- **Gestión de Flota Simplificada**: Seguimiento de vehículos sin métricas complejas

---

## 🏗️ **Arquitectura del Sistema**

### **📋 Componentes Principales**

#### **1. Sistema de Geocercas Específicas**
```python
def poblar_dominios(df: pd.DataFrame) -> None:
    """
    Define y detecta solo las geocercas específicas:
    - Ciudad Mejillones, Oxiquim, Puerto Mejillones
    - Terquim, Interacid, Puerto Angamos
    - TGN, GNLM, Muelle Centinela
    - Excluye: Ruta - Afta Mejillones
    """
```

#### **2. Clasificación de Secuencias**
```python
def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica cada transición en:
    - "viaje_especifico": Entre dos geocercas específicas
    - "viaje_parcial": Incluye una geocerca específica
    - "estadia_interna": Origen = Destino (TGN-TGN)
    - "otro": Incluye geocercas excluidas
    """
```

#### **3. Consolidación de Estadías Internas**
```python
def consolidar_estadias_internas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa transiciones internas con el viaje precedente:
    - Identifica viajes válidos (origen ≠ destino)
    - Extiende duración del viaje precedente
    - Agrega contador de estadías consolidadas
    - Mantiene trazabilidad completa
    """
```

---

## 🔧 **Funcionalidades Específicas**

### **📊 Análisis de Secuencias**

#### **Geocercas Específicas**
```python
GEOCERCAS_ESPECIFICAS = {
    "Ciudad Mejillones", "Oxiquim", "Puerto Mejillones", 
    "Terquim", "Interacid", "Puerto Angamos", 
    "TGN", "GNLM", "Muelle Centinela"
}

GEOCERCAS_EXCLUIDAS = {"Ruta - Afta Mejillones"}
```

#### **Tipos de Secuencias**
- **Viaje Específico**: Entre dos geocercas de la lista específica
- **Viaje Parcial**: Incluye una geocerca específica + otra no específica
- **Estadía Interna**: Mismo origen y destino (ej: TGN-TGN)
- **Otro**: Incluye geocercas excluidas o no específicas

### **🔄 Consolidación Inteligente**

#### **Proceso de Consolidación**
1. **Identificación**: Detecta transiciones internas (origen = destino)
2. **Búsqueda**: Encuentra el viaje válido precedente
3. **Extensión**: Prolonga la duración del viaje válido
4. **Contabilización**: Agrega contador de estadías consolidadas

#### **Ejemplo de Consolidación**
```
Antes:
- Ciudad Mejillones → TGN (viaje válido)
- TGN → TGN (estadía interna)
- TGN → TGN (estadía interna)
- TGN → Puerto Mejillones (viaje válido)

Después:
- Ciudad Mejillones → TGN (viaje válido + 2 estadías consolidadas)
- TGN → Puerto Mejillones (viaje válido)
```

### **📈 Métricas Simplificadas**

#### **Resumen por Vehículo y Geocerca**
- **Viajes por Vehículo**: Cantidad de viajes que cada vehículo hizo a cada geocerca
- **Duración Promedio**: Tiempo promedio de viaje por ruta
- **Frecuencia**: Patrones de movimiento más comunes
- **Eficiencia**: Comparación de tiempos entre vehículos

---

## 📊 **Métricas y KPIs**

### **🎯 Indicadores de Secuencias**
- **Viajes Específicos**: Movimientos entre geocercas objetivo
- **Viajes Parciales**: Movimientos que incluyen una geocerca objetivo
- **Estadías Consolidadas**: Tiempo total en transiciones internas
- **Eficiencia de Rutas**: Optimización de trayectos específicos

### **🚛 Indicadores de Flota**
- **Utilización por Vehículo**: Actividad de cada unidad
- **Patrones de Movimiento**: Rutas más frecuentes
- **Tiempo en Tránsito**: Duración de viajes entre geocercas
- **Frecuencia de Visitas**: Cuántas veces visita cada geocerca

### **📈 Indicadores Geográficos**
- **Cobertura de Geocercas**: Completitud de visitas a objetivos
- **Distribución Espacial**: Balance de actividad entre geocercas
- **Conectividad**: Flujos entre diferentes instalaciones

---

## 🔄 **Flujo de Procesamiento de Datos**

### **1. Preparación de Datos**
```python
def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    # Conversión de timestamps
    # Limpieza de geocercas
    # Ordenamiento por vehículo y tiempo
```

### **2. Definición de Geocercas Específicas**
```python
def poblar_dominios(df: pd.DataFrame) -> None:
    # Detección de geocercas específicas
    # Identificación de geocercas excluidas
    # Clasificación automática
```

### **3. Extracción de Transiciones**
```python
def extraer_transiciones(df: pd.DataFrame) -> pd.DataFrame:
    # Detección de cambios de geocerca
    # Cálculo de duraciones
    # Validación de transiciones
```

### **4. Clasificación de Secuencias**
```python
def clasificar_proceso_con_secuencia(df: pd.DataFrame) -> pd.DataFrame:
    # Identificación de tipos de viaje
    # Clasificación por origen/destino
    # Cálculo de métricas por secuencia
```

### **5. Consolidación de Estadías**
```python
def consolidar_estadias_internas(df: pd.DataFrame) -> pd.DataFrame:
    # Agrupación de transiciones internas
    # Extensión de duraciones
    # Contabilización de consolidaciones
```

---

## 🎨 **Interfaz de Usuario**

### **📊 Dashboard Simplificado**
- **Filtros Básicos**: Por fecha, vehículo (sin filtros de geocerca)
- **Métricas Claras**: Enfoque en secuencias y patrones
- **Visualizaciones Directas**: Gráficos de secuencias y frecuencias

### **📈 Matriz de Secuencias**
- **Origen → Destino**: Visualización de flujos entre geocercas específicas
- **Métricas Agregadas**: Totales y promedios por secuencia
- **Filtros Dinámicos**: Por vehículo y período

### **📋 Resumen por Vehículo**
- **Viajes por Geocerca**: Cuántas veces cada vehículo visitó cada geocerca
- **Duración Promedio**: Tiempo típico por ruta
- **Patrones de Movimiento**: Secuencias más frecuentes

---

## ⚡ **Performance y Optimización**

### **🚀 Optimizaciones Específicas**
- **Procesamiento Simplificado**: Menos cálculos complejos
- **Filtrado Eficiente**: Solo geocercas específicas
- **Consolidación Inteligente**: Reducción de datos redundantes
- **Visualizaciones Optimizadas**: Enfoque en secuencias

### **📊 Métricas de Performance**
- **Tiempo de Carga**: < 3 segundos para datasets típicos
- **Uso de Memoria**: Reducido por simplificación
- **Responsividad**: Interfaz más rápida y directa

---

## 🔧 **Configuración y Personalización**

### **⚙️ Parámetros Globales**
```python
MIN_ESTANCIA_S      = 3  # Tiempo mínimo de estancia
SHIFT_DAY_START     = time(8, 0)   # Inicio turno día
SHIFT_NIGHT_START   = time(20, 0)  # Inicio turno noche
```

### **🎯 Geocercas Configurables**
```python
GEOCERCAS_ESPECIFICAS = {
    "Ciudad Mejillones", "Oxiquim", "Puerto Mejillones",
    "Terquim", "Interacid", "Puerto Angamos",
    "TGN", "GNLM", "Muelle Centinela"
}

GEOCERCAS_EXCLUIDAS = {"Ruta - Afta Mejillones"}
```

---

## 🚀 **Casos de Uso Específicos**

### **👷‍♂️ Para Supervisores de Transporte**
- **Monitoreo de Secuencias**: Patrones de movimiento entre instalaciones
- **Optimización de Rutas**: Identificación de trayectos más eficientes
- **Gestión de Flota**: Distribución de vehículos por geocercas

### **📊 Para Planificación Operacional**
- **Análisis de Patrones**: Tendencias en movimientos entre geocercas
- **Capacidad de Instalaciones**: Frecuencia de visitas a cada geocerca
- **Optimización de Horarios**: Mejores momentos para movimientos

### **🚛 Para Gestión de Flota**
- **Utilización de Vehículos**: Actividad específica por unidad
- **Eficiencia de Rutas**: Comparación de tiempos entre trayectos
- **Planificación de Mantenimiento**: Patrones de uso por vehículo

---

## 🔮 **Roadmap y Mejoras Futuras**

### **🎯 Próximas Funcionalidades**
- **Predicción de Secuencias**: ML para anticipar patrones de movimiento
- **Optimización Automática**: Sugerencias de rutas optimizadas
- **Alertas de Desviación**: Notificaciones cuando se desvían de patrones normales
- **Análisis de Tendencias**: Identificación de cambios en patrones

### **📈 Escalabilidad**
- **Big Data**: Procesamiento de datasets masivos de secuencias
- **Tiempo Real**: Análisis de secuencias en tiempo real
- **API REST**: Integración con sistemas de transporte
- **Mobile App**: Versión móvil para supervisores en campo

---

## 📚 **Referencias Técnicas**

### **🔧 Librerías Utilizadas**
- **Streamlit**: Framework web para dashboards
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Computación numérica
- **Altair**: Visualizaciones estadísticas
- **Folium**: Mapas interactivos

### **📖 Algoritmos Implementados**
- **Clasificación de Secuencias**: Lógica de categorización de viajes
- **Consolidación de Estadías**: Algoritmo de agrupación inteligente
- **Análisis de Patrones**: Identificación de secuencias frecuentes
- **Cálculo de Duraciones**: Procesamiento temporal de transiciones

---

## 🎉 **Conclusión**

**`app7tport.py`** representa una evolución especializada del sistema de análisis de T-Metal, enfocándose específicamente en la visualización y análisis de secuencias de viajes entre geocercas operacionales específicas. Su diseño simplificado y funcionalidades especializadas lo convierten en una herramienta ideal para supervisores de transporte y planificadores operacionales que necesitan una visión clara y directa de los patrones de movimiento de la flota.

### **🎯 Diferencias Clave con app6_mejorado.py**

| Aspecto | app6_mejorado.py | app7tport.py |
|---------|------------------|---------------|
| **Enfoque** | Análisis operacional completo | Secuencias de viajes específicas |
| **Geocercas** | Todas las geocercas detectadas | Solo geocercas específicas predefinidas |
| **Métricas** | Productividad, anomalías, toneladas | Secuencias, patrones, frecuencias |
| **Complejidad** | Alta (múltiples funcionalidades) | Media (enfoque simplificado) |
| **Casos de Uso** | Supervisores, mantenimiento, gestión | Transporte, planificación operacional |
| **Anomalías** | Detección avanzada de detenciones | No incluye análisis de anomalías |
| **Consolidación** | No aplica | Consolidación de estadías internas |

Esta especialización permite a `app7tport.py` proporcionar insights más directos y accionables para roles específicos en la operación de transporte de T-Metal.
