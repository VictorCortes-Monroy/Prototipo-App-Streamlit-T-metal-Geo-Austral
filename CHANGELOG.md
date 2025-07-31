# 📋 Changelog - T-Metal BI Operacional

## [v6.2] - 2024-01-XX - Sistema Completo con Análisis Espacial

### ✨ **Nuevas Funcionalidades Principales**

#### 🗺️ **Análisis de Zonas No Mapeadas**
- **Detección inteligente**: Identifica áreas donde vehículos permanecen fuera de geocercas conocidas
- **Parámetros configurables**: Velocidad máxima (0-20 km/h), tiempo mínimo (5-60 min), radio de agrupación (5-50 m)
- **Clustering espacial**: Agrupación automática de zonas cercanas usando DBSCAN + Haversine
- **Visualización interactiva**: Mapa con Folium mostrando geocercas conocidas (🟢) y zonas candidatas (🔴🟠)
- **Métricas detalladas**: Duración, vehículos involucrados, coordenadas centrales, radio aproximado

#### 🍽️ **Geocerca Casino**
- **Detección automática**: Reconoce geocercas que contengan "casino" (insensible a mayúsculas)
- **Clasificación no operacional**: Todos los viajes hacia/desde Casino = "otro"
- **Integración completa**: Incluida en GEOCERCAS_NO_OPERACIONALES junto con Instalaciones de Faena
- **Visualización**: Nueva sección "🍽️ Casino" en dashboard de geocercas detectadas

#### 🪨 **Estimación de Toneladas Simplificada**
- **Metodología fija**: 42 toneladas exactas por viaje de producción (carga/descarga)
- **Cálculos determinísticos**: Eliminada variabilidad aleatoria de distribución normal
- **Métricas consistentes**: Reportes idénticos y reproducibles entre sesiones
- **Fórmula**: `Total Toneladas = Viajes Producción × 42`

#### 🎛️ **Dashboard Completamente Reorganizado**
- **Filtros expandidos**: 5 columnas (Fecha, Vehículo, Turno, Geocerca Origen, Geocerca Destino)
- **Matriz de producción con pestañas**:
  - **📊 Matriz General**: Vista global origen-destino con totales
  - **🚛 Detalle por Vehículo**: Análisis individual con selector de vehículo
- **Elements removidos**: Gráfico de distribución de tiempos, métricas de productividad, aviso de detecciones
- **Diagnóstico DESCONOCIDO**: Análisis detallado de viajes sin origen/destino identificado

### 🔧 **Mejoras Técnicas Avanzadas**

#### 📊 **Procesamiento de Datos Inteligente**
- **Filtrado GPS de dos niveles**:
  - `MIN_ESTANCIA_S = 3`: Filtro inicial para captura
  - `UMBRAL_PERMANENCIA_REAL = 60`: Filtro inteligente para eliminar ruido GPS
- **Reconstrucción de transiciones**: Lógica avanzada para detectar movimientos `Geocerca1 → [VIAJE] → Geocerca2`
- **Clasificación con secuencias**: Contexto de proceso anterior para clasificación precisa de retornos
- **Agrupación lógica**: `GEOCERCAS_NO_OPERACIONALES = INSTALACIONES_FAENA ∪ CASINO`

#### 🗺️ **Algoritmos de Análisis Espacial**
- **Distancia Haversine**: Cálculo preciso de distancias esféricas entre coordenadas GPS
- **Clustering DBSCAN**: Agrupación espacial con métrica haversine y parámetros configurables
- **Centro ponderado**: Cálculo de centros de zona ponderados por duración de permanencia
- **Radio dinámico**: Cálculo automático del radio real de clusters basado en distancias máximas
- **Mapas interactivos**: Integración completa Folium + Streamlit-Folium con popups informativos

#### 💾 **Sistema de Exportación Completo**
- **7 hojas Excel**: Transiciones, TiemposViaje, MetricasViaje, CiclosMejorados, ProduccionHoraria, ToneladasEstimadas, ResumenTipos
- **Datos de clustering**: Información de zonas agrupadas y métricas espaciales
- **Formato profesional**: Headers formateados, datos filtrados según selección usuario

### 🐛 **Correcciones Críticas**

#### **Sistema de Clasificación**
- **Prioridad máxima geocercas no operacionales**: Instalaciones de Faena y Casino tienen precedencia absoluta
- **Secuencias de retorno corregidas**: 
  - Retorno post-descarga: `Botadero → Módulo/Pila ROM` (sin requerir carga previa)
  - Retorno post-carga: `Módulo/Pila ROM → Stock` (requiere carga previa)
- **Eliminación ruido GPS**: Filtro inteligente de permanencias < 60 segundos

#### **Detección y Análisis de Viajes**
- **Algoritmo origen/destino mejorado**: Búsqueda expandida en todo el DataFrame del vehículo
- **Diagnóstico casos DESCONOCIDO**: Identificación y categorización de viajes problemáticos
- **Logging detallado**: Sistema de debugging con información de casos edge
- **Reconstrucción transiciones**: Lógica robusta para capturar todos los tipos de movimiento

#### **Errores de Sistema Resueltos**
- **StreamlitSetPageConfigMustBeFirstCommandError**: Aplicación auto-contenida sin imports problemáticos
- **KeyError 'Geocerca'**: Corrección definitiva usando nombre correcto de columna 'Geocercas'
- **Nombres de columnas**: Mejorada claridad en "Métricas Detalladas por Vehículo"
- **Índices desalineados**: Corrección en clasificación con secuencias por vehículo

### 📚 **Documentación Completa Nueva**

#### **Guías de Usuario**
- **GUIA_USUARIO_COMPLETA.md**: 
  - Introducción completa al sistema
  - Especificación detallada de formato de entrada
  - Explicación de todos los tipos de geocercas
  - Guía paso a paso de uso del dashboard
  - Solución de problemas comunes

#### **Documentación Técnica**
- **DOCUMENTACION_DESARROLLADOR.md**:
  - Arquitectura completa del sistema
  - Algoritmos detallados con código
  - Guías de extensibilidad
  - Mejores prácticas de performance
  - Referencias de debugging

#### **Actualizaciones de Documentación Existente**
- **README.md**: Agregados nuevos tipos de geocercas y funcionalidades
- **DOCUMENTACION_TECNICA.md**: Actualizada con algoritmos de clustering y clasificación
- **ESPECIFICACION_INPUT.md**: Mantenida consistencia con todos los cambios

### 🔧 **Dependencias y Requisitos**

#### **Nuevas Dependencias Críticas**
```
streamlit-folium==0.22.0  # Mapas interactivos con Folium
scikit-learn==1.5.2       # Algoritmos de clustering DBSCAN
```

#### **Stack Tecnológico Completo**
- **Frontend**: Streamlit con componentes interactivos
- **Procesamiento**: Pandas + NumPy para análisis de datos
- **Visualización**: Altair para gráficos, Folium para mapas
- **Análisis Espacial**: Scikit-learn DBSCAN con métrica Haversine
- **Exportación**: XlsxWriter para reportes Excel profesionales

---

## [v2.0.0] - 2025-07-23

### 🎉 **Nuevas Funcionalidades**

#### **🌅🌙 Sistema de Turnos**
- ✅ **Filtro por turno**: Nuevo selector para filtrar por turno día (8:00-20:00) o noche (20:00-8:00)
- ✅ **Métricas por turno**: Estadísticas separadas para cada turno con fechas involucradas
- ✅ **Visualizaciones diferenciadas**: Gráficos con colores específicos por turno
- ✅ **Información contextual**: Definición clara de horarios de turnos en la interfaz

#### **🏗️ Integración de Pilas ROM**
- ✅ **Detección automática**: Soporte para "Pila Rom 1", "Pila Rom 2", "Pila Rom 3"
- ✅ **Clasificación ampliada**: Las pilas ROM se tratan como áreas de carga adicionales
- ✅ **Procesos actualizados**: 
  - Carga: STOCKS → MODULES **o** PILAS_ROM
  - Descarga: MODULES **o** PILAS_ROM → BOTADEROS
  - Retorno: MODULES **o** PILAS_ROM → STOCKS

#### **📊 Concepto de Producción Mejorado**
- ✅ **Producción ampliada**: Tanto carga como descarga se consideran producción
- ✅ **Gráficos combinados**: Líneas separadas para carga (azul) y descarga (naranja)
- ✅ **Métricas actualizadas**: Total producción = Carga + Descarga

### 🔧 **Mejoras en la Interfaz**

#### **📈 Visualizaciones Mejoradas**
- ✅ **Gráfico de producción horaria**: Dos líneas diferenciadas por color
- ✅ **Gráfico de toneladas**: Barras apiladas por tipo de proceso
- ✅ **Gráfico por turnos**: Círculos diferenciados por turno día/noche
- ✅ **Colores consistentes**: Paleta de colores unificada en toda la aplicación

#### **📋 Conteo Detallado de Viajes**
- ✅ **Tabla mejorada**: Muestra cantidad y porcentaje de cada tipo de viaje
- ✅ **Métricas destacadas**: 4 columnas con conteos específicos
- ✅ **Información adicional**: 
  - Total viajes de producción (carga + descarga)
  - Total viajes operacionales
  - Porcentaje de eficiencia

#### **🪨 Estimación de Toneladas Actualizada**
- ✅ **Producción completa**: Incluye tanto carga como descarga
- ✅ **Gráfico apilado**: Diferenciación visual por tipo de proceso
- ✅ **Estadísticas separadas**: Toneladas por tipo de proceso

### 🐛 **Correcciones Técnicas**

#### **⚠️ Advertencias de Pandas**
- ✅ **FutureWarning corregido**: Uso de parámetros nombrados en `to_excel()`
- ✅ **Compatibilidad**: Preparado para pandas 3.0+

#### **🧪 Pruebas Automatizadas**
- ✅ **Script de pruebas**: `test_app5.py` con validación completa
- ✅ **Datos de prueba**: `datos_prueba.csv` con casos realistas
- ✅ **Checklist manual**: `CHECKLIST_PRUEBAS.md` para validación exhaustiva

### 📁 **Archivos Nuevos**

- `test_app5.py` - Script de pruebas automatizadas
- `datos_prueba.csv` - Datos de prueba con todas las geocercas
- `CHECKLIST_PRUEBAS.md` - Checklist completo de pruebas manuales
- `CHANGELOG.md` - Este archivo de documentación

### 🔄 **Archivos Modificados**

- `app5.py` - Aplicación principal con todas las nuevas funcionalidades
- `requirements.txt` - Dependencias actualizadas

### 🎯 **Beneficios de los Cambios**

1. **Análisis más completo**: Incluye turnos y pilas ROM en el análisis
2. **Mejor toma de decisiones**: Métricas diferenciadas por turno
3. **Flexibilidad operacional**: Soporte para diferentes tipos de áreas de carga
4. **Interfaz más clara**: Información detallada y visualizaciones mejoradas
5. **Preparación para producción**: Pruebas exhaustivas y documentación completa

### 🚀 **Compatibilidad**

- ✅ **Datos existentes**: Compatible con archivos CSV actuales
- ✅ **Funcionalidades anteriores**: Todas las funcionalidades previas se mantienen
- ✅ **Nuevas geocercas**: Detección automática sin configuración manual

### 📊 **Métricas de Calidad**

- ✅ **Pruebas automatizadas**: 100% pasando
- ✅ **Funcionalidades validadas**: Todas las nuevas características probadas
- ✅ **Documentación**: Completa y actualizada
- ✅ **Rendimiento**: Optimizado para datos grandes

---

## [v1.0.0] - 2025-06-25

### 🎯 **Funcionalidades Iniciales**
- ✅ Carga de datos CSV desde GeoAustral
- ✅ Detección automática de geocercas (Stocks, Módulos, Botaderos)
- ✅ Análisis de transiciones entre geocercas
- ✅ Clasificación de procesos (carga, retorno, descarga)
- ✅ Detección de ciclos completos
- ✅ Métricas de productividad
- ✅ Estimación de toneladas
- ✅ Exportación a Excel
- ✅ Filtros por fecha y vehículo

---

## 📝 **Notas de Desarrollo**

### **Equipo de Desarrollo**
- **Desarrollador**: Asistente AI
- **Cliente**: T-Metal
- **Proyecto**: BI Operacional

### **Tecnologías Utilizadas**
- **Frontend**: Streamlit 1.45.1
- **Procesamiento**: Pandas 2.2.3, NumPy 2.2.6
- **Visualización**: Altair 5.5.0
- **Exportación**: XlsxWriter 3.2.3

### **Próximas Mejoras Sugeridas**
- [ ] Dashboard en tiempo real
- [ ] Alertas automáticas
- [ ] Integración con sistemas externos
- [ ] Reportes automáticos por email
- [ ] Análisis predictivo de productividad 