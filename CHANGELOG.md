# 📋 Changelog - T-Metal BI Operacional

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