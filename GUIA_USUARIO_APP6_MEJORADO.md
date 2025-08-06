# 👥 **GUÍA DE USUARIO - T-Metal BI Operacional v6.0**

## 🎯 **Descripción General**

Esta guía está diseñada para usuarios de **`app6_mejorado.py`**, la aplicación principal de análisis operacional de T-Metal que proporciona insights completos sobre la operación minera, incluyendo análisis de productividad, detección de anomalías, y optimización de procesos.

---

## 🚀 **Inicio Rápido**

### **📥 Cargar Datos**
1. **Preparar archivo CSV** con las siguientes columnas:
   - `Nombre del Vehículo`: Identificador del vehículo
   - `Tiempo de evento`: Timestamp (YYYY-MM-DD HH:MM:SS)
   - `Geocercas`: Nombre de la geocerca (vacío = en viaje)
   - `Velocidad [km/h]`: Velocidad del vehículo (opcional)
   - `Latitud/Longitud`: Coordenadas GPS (opcional)

2. **Hacer clic en "Browse files"** y seleccionar el archivo CSV

3. **Esperar procesamiento** (2-5 segundos para archivos típicos)

---

## 📊 **Navegación por Secciones**

### **🏭 1. Geocercas Detectadas**
**Propósito**: Ver qué geocercas fueron identificadas automáticamente

**Información mostrada**:
- ✅ **Geocercas Clasificadas**: Stocks, módulos, botaderos, pilas ROM
- ❓ **Geocercas No Clasificadas**: Rutas y geocercas no operacionales
- 📊 **Estadísticas**: Cantidad por categoría

**Acciones disponibles**:
- Revisar clasificación automática
- Identificar geocercas que necesitan atención

---

### **🔍 2. Filtros de Análisis**
**Propósito**: Configurar el análisis según necesidades específicas

**Filtros disponibles**:
- **📅 Fecha**: Seleccionar período de análisis
- **🚛 Vehículo**: Filtrar por vehículo específico
- **🏭 Geocerca Origen**: Filtrar por punto de partida
- **🎯 Geocerca Destino**: Filtrar por punto de llegada
- **🌞 Turno**: Día (08:00-19:59) o Noche (20:00-07:59)

**Cómo usar**:
1. Seleccionar filtros deseados
2. Los datos se actualizan automáticamente
3. Combinar múltiples filtros para análisis específicos

---

### **📊 3. Matriz de Viajes de Carga/Descarga**
**Propósito**: Visualizar flujos de carga y descarga entre geocercas

**Información mostrada**:
- **Tabla de transiciones**: Origen → Destino con métricas
- **Gráfico de barras**: Viajes por tipo de proceso
- **Gráfico de líneas**: Tendencias temporales

**Métricas incluidas**:
- Cantidad de viajes por tipo
- Duración promedio
- Tiempo total por proceso

**Acciones disponibles**:
- Exportar datos a Excel
- Filtrar por tipo de proceso
- Analizar tendencias temporales

---

### **⏱️ 4. Análisis de Tiempos de Viaje**
**Propósito**: Analizar duración y eficiencia de viajes

**Información mostrada**:
- **Estadísticas por proceso**: Media, mediana, desviación estándar
- **Gráfico de distribución**: Histograma de duraciones
- **Tabla detallada**: Todos los viajes con métricas

**Análisis disponible**:
- Comparar eficiencia entre vehículos
- Identificar viajes anómalos
- Analizar patrones por turno

---

### **📈 5. Análisis Detallado de Viajes por Hora**
**Propósito**: Analizar productividad por hora del día

**Información mostrada**:
- **Gráfico de calor**: Actividad por hora y día
- **Estadísticas por hora**: Promedios y totales
- **Comparación turnos**: Día vs Noche

**Insights obtenibles**:
- Horas pico de actividad
- Patrones de productividad
- Oportunidades de optimización

---

### **💰 6. Toneladas Acumuladas (Estimadas)**
**Propósito**: Estimar producción basada en patrones de viajes

**Información mostrada**:
- **Gráfico de acumulación**: Toneladas estimadas por día
- **Estadísticas por turno**: Producción día vs noche
- **Proyecciones**: Tendencias de producción

**Nota**: Las estimaciones se basan en patrones históricos y pueden requerir calibración.

---

### **🚨 7. Análisis de Detenciones Anómalas**
**Propósito**: Identificar detenciones inusuales que requieren atención

**Criterios de detección**:
- Velocidad < 2 km/h por > 10 minutos
- Duración > promedio + 2σ de la geocerca
- Solo geocercas operacionales

**Información mostrada**:
- **Métricas generales**: Total de detenciones anómalas
- **Tabla detallada**: Vehículo, geocerca, duración, severidad
- **Gráficos**: Distribución por severidad y geocerca

**Clasificación por severidad**:
- 🔴 **Alta**: > 3σ del promedio (atención inmediata)
- 🟡 **Media**: 2-3σ del promedio (monitoreo)

**Acciones recomendadas**:
- Revisar vehículos con detenciones de alta severidad
- Analizar patrones por geocerca
- Planificar mantenimiento preventivo

---

### **🗺️ 8. Análisis de Zonas No Mapeadas**
**Propósito**: Identificar áreas de actividad no registradas

**Criterios de detección**:
- Velocidad < 5 km/h
- Tiempo mínimo de 10 minutos
- Agrupación por proximidad (10 metros)

**Información mostrada**:
- **Mapa de calor**: Visualización geográfica de zonas
- **Tabla de clusters**: Coordenadas y métricas
- **Estadísticas**: Cantidad y distribución de zonas

**Uso operacional**:
- Identificar rutas no registradas
- Optimizar cobertura de geocercas
- Mejorar planificación de rutas

---

### **📋 9. Resumen de Viajes por Tipo**
**Propósito**: Vista general de la actividad operacional

**Información mostrada**:
- **KPIs principales**: Totales por tipo de proceso
- **Gráfico de pastel**: Distribución porcentual
- **Estadísticas por vehículo**: Actividad individual

**Métricas incluidas**:
- Total de viajes por tipo
- Tiempo total por proceso
- Promedios y eficiencias

---

## 🔧 **Funcionalidades Avanzadas**

### **📊 Exportación de Datos**
**Ubicación**: Sección "Matriz de Viajes de Carga/Descarga"

**Formatos disponibles**:
- **Excel (.xlsx)**: Con múltiples hojas
- **CSV**: Datos procesados

**Contenido exportado**:
- Transiciones filtradas
- Métricas calculadas
- Datos de anomalías

### **🗺️ Visualización Geográfica**
**Ubicación**: Sección "Análisis de Zonas No Mapeadas"

**Características**:
- **Zoom interactivo**: Acercar/alejar
- **Filtros dinámicos**: Por cluster
- **Información detallada**: Al hacer clic en puntos

### **📈 Análisis Temporal**
**Disponible en**: Múltiples secciones

**Funcionalidades**:
- **Filtros por fecha**: Períodos específicos
- **Comparación de turnos**: Día vs Noche
- **Tendencias temporales**: Patrones por hora/día

---

## 🎯 **Casos de Uso por Rol**

### **👷‍♂️ Para Supervisores de Operaciones**

#### **Monitoreo Diario**
1. **Revisar "Resumen de Viajes"** para KPIs generales
2. **Analizar "Matriz de Viajes"** para flujos operacionales
3. **Verificar "Detenciones Anómalas"** para problemas urgentes
4. **Revisar "Análisis Horario"** para patrones de productividad

#### **Análisis de Problemas**
1. **Identificar vehículos con detenciones anómalas**
2. **Analizar geocercas problemáticas**
3. **Comparar eficiencia entre turnos**
4. **Revisar zonas no mapeadas para optimización**

### **🔧 Para Mantenimiento**

#### **Detección de Fallas**
1. **Revisar "Detenciones Anómalas"** por severidad
2. **Analizar patrones por vehículo**
3. **Identificar geocercas con problemas recurrentes**
4. **Planificar mantenimiento preventivo**

#### **Optimización de Rutas**
1. **Analizar "Zonas No Mapeadas"** para rutas no registradas
2. **Revisar tiempos de viaje anómalos**
3. **Identificar cuellos de botella operacionales**

### **📊 Para Gestión**

#### **Reportes de Productividad**
1. **Exportar datos de "Matriz de Viajes"**
2. **Analizar "Toneladas Estimadas"** para producción
3. **Revisar "Resumen de Viajes"** para KPIs generales
4. **Comparar eficiencia entre períodos**

#### **Toma de Decisiones**
1. **Identificar oportunidades de optimización**
2. **Analizar impacto de cambios operacionales**
3. **Planificar inversiones en flota**
4. **Evaluar eficiencia de geocercas**

---

## ⚠️ **Solución de Problemas**

### **🔍 Problemas Comunes**

#### **"No se detectan geocercas"**
- **Causa**: Formato incorrecto en columna "Geocercas"
- **Solución**: Verificar que la columna contenga nombres válidos
- **Prevención**: Usar nombres estándar de geocercas

#### **"Detenciones anómalas no aparecen"**
- **Causa**: Datos de velocidad faltantes o incorrectos
- **Solución**: Verificar columna "Velocidad [km/h]"
- **Prevención**: Asegurar calidad de datos GPS

#### **"Aplicación lenta"**
- **Causa**: Archivo muy grande o datos complejos
- **Solución**: Filtrar por fecha o vehículo específico
- **Prevención**: Procesar archivos de tamaño moderado

#### **"Errores en exportación"**
- **Causa**: Datos incompletos o formato incorrecto
- **Solución**: Verificar integridad de datos antes de exportar
- **Prevención**: Validar datos de entrada

### **📞 Soporte Técnico**

#### **Información para Reportes**
- **Versión de la aplicación**: 6.0 Mejorado
- **Archivo de datos**: Tamaño y formato
- **Error específico**: Mensaje completo
- **Pasos para reproducir**: Secuencia exacta

#### **Contactos**
- **Desarrollo**: Equipo técnico interno
- **Documentación**: Esta guía y documentación técnica
- **Actualizaciones**: Repositorio GitHub

---

## 🎓 **Mejores Prácticas**

### **📊 Para Análisis Efectivo**

1. **Usar filtros específicos** para análisis focalizados
2. **Exportar datos** para análisis externos
3. **Revisar anomalías** regularmente
4. **Comparar períodos** para identificar tendencias

### **🔧 Para Mantenimiento**

1. **Monitorear detenciones anómalas** diariamente
2. **Analizar patrones por vehículo** semanalmente
3. **Revisar zonas no mapeadas** mensualmente
4. **Actualizar geocercas** según necesidades

### **📈 Para Optimización**

1. **Identificar cuellos de botella** en flujos operacionales
2. **Analizar eficiencia por turno** para optimizar horarios
3. **Revisar tiempos de viaje** para mejorar rutas
4. **Evaluar cobertura de geocercas** para completitud

---

## 🔮 **Próximas Funcionalidades**

### **🎯 En Desarrollo**
- **Alertas automáticas** para detenciones críticas
- **Predicción de fallas** usando machine learning
- **Integración con sistemas ERP** para datos en tiempo real
- **Versión móvil** para supervisores en campo

### **📈 Mejoras Planificadas**
- **Análisis predictivo** de productividad
- **Optimización automática** de rutas
- **Dashboard ejecutivo** con KPIs consolidados
- **API REST** para integración con otros sistemas

---

## 🎉 **Conclusión**

**`app6_mejorado.py`** es una herramienta poderosa para el análisis operacional completo de T-Metal. Su combinación de análisis tradicional de productividad con tecnologías avanzadas de detección de anomalías proporciona insights valiosos para la toma de decisiones operacionales.

**Recuerda**: La efectividad del análisis depende de la calidad de los datos de entrada. Mantén actualizada la información y revisa regularmente los resultados para maximizar el valor operacional.

---

*Última actualización: Enero 2025*  
*Versión: 6.0 Mejorado*  
*Documentación específica para análisis operacional completo*
