# 🚛 **GUÍA DE USUARIO - T-Metal Análisis de Secuencias de Viajes v7.0**

## 🎯 **Descripción General**

Esta guía está diseñada para usuarios de **`app7tport.py`**, la aplicación especializada en análisis de secuencias de viajes entre geocercas específicas. Esta herramienta proporciona una visualización clara y simplificada de los patrones de movimiento de la flota minera, eliminando la complejidad de métricas operacionales tradicionales.

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

3. **Esperar procesamiento** (1-3 segundos para archivos típicos)

---

## 📊 **Navegación por Secciones**

### **🏭 1. Geocercas Específicas Detectadas**
**Propósito**: Ver qué geocercas específicas fueron identificadas

**Geocercas Objetivo**:
- ✅ **Ciudad Mejillones**: Centro urbano
- ✅ **Oxiquim**: Instalación industrial
- ✅ **Puerto Mejillones**: Terminal portuario
- ✅ **Terquim**: Instalación química
- ✅ **Interacid**: Instalación industrial
- ✅ **Puerto Angamos**: Terminal portuario
- ✅ **TGN**: Terminal de gas natural
- ✅ **GNLM**: Gas natural licuado
- ✅ **Muelle Centinela**: Instalación portuaria

**Geocercas Excluidas**:
- ❌ **Ruta - Afta Mejillones**: Ruta de transporte (no analizada)

**Información mostrada**:
- **Geocercas Encontradas**: Cantidad de geocercas objetivo detectadas
- **Geocercas No Encontradas**: Geocercas objetivo no presentes en datos
- **Geocercas Excluidas Encontradas**: Rutas identificadas

---

### **🔍 2. Filtros de Análisis**
**Propósito**: Configurar el análisis según necesidades específicas

**Filtros disponibles**:
- **📅 Fecha**: Seleccionar período de análisis
- **🚛 Vehículo**: Filtrar por vehículo específico

**Nota**: No hay filtros de geocerca origen/destino ni turno, ya que el enfoque es en secuencias completas.

**Cómo usar**:
1. Seleccionar filtros deseados
2. Los datos se actualizan automáticamente
3. Los resultados muestran secuencias completas

---

### **📊 3. Matriz de Secuencias de Viajes**
**Propósito**: Visualizar flujos de viajes entre geocercas específicas

**Información mostrada**:
- **Tabla de transiciones**: Origen → Destino con métricas
- **Gráfico de barras**: Viajes por tipo de secuencia
- **Gráfico de líneas**: Tendencias temporales

**Tipos de Secuencias**:
- **Viajes Específicos**: Entre dos geocercas de la lista objetivo
- **Viajes Parciales**: Incluye una geocerca objetivo + otra no específica
- **Estadías Internas**: Mismo origen y destino (consolidadas)
- **Otros**: Incluye geocercas excluidas

**Métricas incluidas**:
- Cantidad de viajes por tipo
- Duración promedio
- Tiempo total por secuencia
- Estadías consolidadas

**Acciones disponibles**:
- Exportar datos a Excel
- Filtrar por tipo de secuencia
- Analizar tendencias temporales

---

### **⏱️ 4. Análisis de Tiempos de Viaje**
**Propósito**: Analizar duración y eficiencia de secuencias de viajes

**Información mostrada**:
- **Estadísticas por secuencia**: Media, mediana, desviación estándar
- **Gráfico de distribución**: Histograma de duraciones
- **Tabla detallada**: Todas las secuencias con métricas

**Análisis disponible**:
- Comparar eficiencia entre vehículos
- Identificar secuencias anómalas
- Analizar patrones de consolidación

---

### **📈 5. Análisis Horario de Secuencias**
**Propósito**: Analizar patrones de secuencias por hora del día

**Información mostrada**:
- **Gráfico de calor**: Actividad por hora y día
- **Estadísticas por hora**: Promedios y totales
- **Comparación de secuencias**: Específicas vs Parciales

**Insights obtenibles**:
- Horas pico de actividad entre geocercas
- Patrones de secuencias por hora
- Oportunidades de optimización de rutas

---

### **📋 6. Resumen de Viajes por Vehículo y Geocerca**
**Propósito**: Vista detallada de actividad por vehículo y geocerca específica

**Información mostrada**:
- **Tabla por vehículo**: Cantidad de viajes a cada geocerca
- **Gráfico de barras**: Viajes por vehículo
- **Gráfico de pastel**: Distribución por geocerca
- **Estadísticas agregadas**: Totales y promedios

**Métricas incluidas**:
- Viajes por vehículo a cada geocerca
- Duración promedio por ruta
- Frecuencia de visitas
- Eficiencia comparativa

---

## 🔧 **Funcionalidades Específicas**

### **🔄 Consolidación de Estadías Internas**
**Propósito**: Agrupar transiciones internas (ej: TGN-TGN) con el viaje precedente

**Proceso automático**:
1. **Identificación**: Detecta transiciones donde origen = destino
2. **Búsqueda**: Encuentra el viaje válido precedente
3. **Extensión**: Prolonga la duración del viaje válido
4. **Contabilización**: Agrega contador de estadías consolidadas

**Ejemplo visual**:
```
Antes de consolidación:
- Ciudad Mejillones → TGN (viaje válido, 30 min)
- TGN → TGN (estadía interna, 15 min)
- TGN → TGN (estadía interna, 20 min)
- TGN → Puerto Mejillones (viaje válido, 45 min)

Después de consolidación:
- Ciudad Mejillones → TGN (viaje válido, 65 min, +2 estadías)
- TGN → Puerto Mejillones (viaje válido, 45 min)
```

**Beneficios**:
- Elimina ruido en análisis de secuencias
- Mantiene trazabilidad completa
- Simplifica visualización de patrones

---

### **📊 Exportación de Datos**
**Ubicación**: Sección "Matriz de Secuencias de Viajes"

**Formatos disponibles**:
- **Excel (.xlsx)**: Con múltiples hojas
- **CSV**: Datos procesados

**Contenido exportado**:
- Secuencias filtradas
- Métricas calculadas
- Datos de consolidación

---

## 🎯 **Casos de Uso por Rol**

### **🚛 Para Supervisores de Transporte**

#### **Monitoreo de Secuencias**
1. **Revisar "Matriz de Secuencias"** para flujos principales
2. **Analizar "Resumen por Vehículo"** para actividad individual
3. **Verificar "Análisis Horario"** para patrones temporales
4. **Exportar datos** para reportes detallados

#### **Optimización de Rutas**
1. **Identificar secuencias más frecuentes**
2. **Analizar tiempos de viaje anómalos**
3. **Revisar consolidación de estadías**
4. **Planificar optimización de rutas**

### **📊 Para Planificación Operacional**

#### **Análisis de Patrones**
1. **Revisar "Resumen por Vehículo"** para distribución de carga
2. **Analizar "Matriz de Secuencias"** para flujos principales
3. **Identificar geocercas con mayor actividad**
4. **Planificar capacidad de instalaciones**

#### **Optimización de Horarios**
1. **Revisar "Análisis Horario"** para horas pico
2. **Analizar patrones por día de la semana**
3. **Identificar oportunidades de optimización**
4. **Planificar mantenimiento de flota**

### **👷‍♂️ Para Operadores de Campo**

#### **Seguimiento de Vehículos**
1. **Revisar "Resumen por Vehículo"** para actividad específica
2. **Analizar secuencias por vehículo**
3. **Identificar patrones de movimiento**
4. **Optimizar asignación de tareas**

---

## ⚠️ **Solución de Problemas**

### **🔍 Problemas Comunes**

#### **"No se detectan geocercas específicas"**
- **Causa**: Nombres de geocercas no coinciden exactamente
- **Solución**: Verificar nombres en la lista de geocercas objetivo
- **Prevención**: Usar nombres estándar de geocercas

#### **"Secuencias no aparecen"**
- **Causa**: Datos no contienen geocercas específicas
- **Solución**: Verificar que los datos incluyan geocercas objetivo
- **Prevención**: Asegurar calidad de datos de entrada

#### **"Consolidación no funciona"**
- **Causa**: Datos no tienen transiciones internas
- **Solución**: Verificar que existan registros con origen = destino
- **Prevención**: Validar integridad de datos GPS

#### **"Aplicación lenta"**
- **Causa**: Archivo muy grande o datos complejos
- **Solución**: Filtrar por fecha o vehículo específico
- **Prevención**: Procesar archivos de tamaño moderado

### **📞 Soporte Técnico**

#### **Información para Reportes**
- **Versión de la aplicación**: 7.0 Transporte
- **Archivo de datos**: Tamaño y formato
- **Error específico**: Mensaje completo
- **Pasos para reproducir**: Secuencia exacta

#### **Contactos**
- **Desarrollo**: Equipo técnico interno
- **Documentación**: Esta guía y documentación técnica
- **Actualizaciones**: Repositorio GitHub

---

## 🎓 **Mejores Prácticas**

### **📊 Para Análisis de Secuencias**

1. **Usar filtros específicos** para análisis focalizados
2. **Revisar consolidación** para entender patrones reales
3. **Exportar datos** para análisis externos
4. **Comparar períodos** para identificar tendencias

### **🚛 Para Gestión de Transporte**

1. **Monitorear secuencias frecuentes** diariamente
2. **Analizar patrones por vehículo** semanalmente
3. **Revisar consolidación de estadías** mensualmente
4. **Optimizar rutas** basándose en patrones

### **📈 Para Optimización**

1. **Identificar secuencias más eficientes** en tiempos de viaje
2. **Analizar distribución de carga** entre geocercas
3. **Revisar patrones horarios** para optimizar horarios
4. **Evaluar cobertura de geocercas** para completitud

---

## 🔮 **Próximas Funcionalidades**

### **🎯 En Desarrollo**
- **Predicción de secuencias** usando machine learning
- **Optimización automática** de rutas
- **Alertas de desviación** de patrones normales
- **Análisis de tendencias** de secuencias

### **📈 Mejoras Planificadas**
- **Análisis predictivo** de patrones de movimiento
- **Sugerencias automáticas** de optimización
- **Dashboard ejecutivo** con KPIs de secuencias
- **API REST** para integración con sistemas de transporte

---

## 🎉 **Conclusión**

**`app7tport.py`** es una herramienta especializada para el análisis de secuencias de viajes entre geocercas específicas de T-Metal. Su diseño simplificado y funcionalidades especializadas proporcionan insights directos y accionables para supervisores de transporte y planificadores operacionales.

**Recuerda**: El análisis de secuencias es más efectivo cuando se combina con conocimiento operacional específico. Revisa regularmente los patrones y ajusta las estrategias según los insights obtenidos.

---

## 📋 **Comparación con app6_mejorado.py**

| Aspecto | app6_mejorado.py | app7tport.py |
|---------|------------------|---------------|
| **Enfoque** | Análisis operacional completo | Secuencias de viajes específicas |
| **Geocercas** | Todas las detectadas | Solo geocercas específicas predefinidas |
| **Métricas** | Productividad, anomalías, toneladas | Secuencias, patrones, frecuencias |
| **Complejidad** | Alta (múltiples funcionalidades) | Media (enfoque simplificado) |
| **Casos de Uso** | Supervisores, mantenimiento, gestión | Transporte, planificación operacional |
| **Anomalías** | Detección avanzada de detenciones | No incluye análisis de anomalías |
| **Consolidación** | No aplica | Consolidación de estadías internas |

**Elige según tu necesidad**:
- **app6_mejorado.py**: Para análisis operacional completo con detección de anomalías
- **app7tport.py**: Para análisis especializado de secuencias de viajes

---

*Última actualización: Enero 2025*  
*Versión: 7.0 Transporte*  
*Documentación específica para análisis de secuencias de viajes*
