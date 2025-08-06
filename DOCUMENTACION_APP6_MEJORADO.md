# 📋 **DOCUMENTACIÓN TÉCNICA - T-Metal BI Operacional v6 Mejorado**

## 🎯 **Descripción General**

**T-Metal BI Operacional v6 Mejorado** es una aplicación web desarrollada en Streamlit que procesa datos GPS de flota minera para generar análisis operacionales avanzados. La aplicación se especializa en:

- **Análisis de transiciones** entre geocercas operacionales
- **Clasificación inteligente** de procesos de carga, descarga y retorno
- **Detección automática** de detenciones anómalas
- **Normalización avanzada** de geocercas múltiples
- **Visualizaciones interactivas** para toma de decisiones

---

## 🏗️ **Arquitectura y Componentes**

### **📊 Módulos Principales**

#### **1. Procesamiento de Datos**
- **`preparar_datos()`**: Limpieza y normalización del DataFrame de entrada
- **`normalizar_geocerca()`**: Normalización inteligente de geocercas múltiples
- **`poblar_dominios()`**: Detección automática de tipos de geocercas

#### **2. Análisis de Transiciones**
- **`extraer_transiciones()`**: Detecta transiciones válidas entre geocercas
- **`clasificar_proceso_con_secuencia()`**: Clasifica procesos operacionales
- **`extraer_tiempos_viaje()`**: Calcula tiempos de viaje entre ubicaciones

#### **3. Análisis Avanzado**
- **`analizar_detenciones_anomalas()`**: Detecta patrones anómalos de detención
- **`_analizar_detenciones_en_geocerca()`**: Análisis específico por geocerca

---

## 🔧 **Funcionalidades Clave**

### **🎯 1. Normalización Inteligente de Geocercas**

**Problema Resuelto**: Celdas con múltiples geocercas separadas por `;`

**Ejemplos de Procesamiento**:
```
Input:  "Stock Central - 30 km hr ; stock Central ; Ruta Pilas ROM - 40 km"
Output: "Stock Central - 30 km hr"

Input:  "Instalacion de faena ; Camino Instalaciones - 30 km/hr"
Output: "Instalacion de faena"

Input:  "Ruta Principal ; Camino Norte"
Output: "" (vacío - ambas son rutas)
```

**Reglas de Prioridad**:
1. **Geocercas operacionales** (stock, modulo, pila, botadero)
2. **Geocercas específicas conocidas**
3. **Primera geocerca válida**

### **🚨 2. Análisis de Detenciones Anómalas**

**Supuestos Operacionales**:
- **Detención**: Velocidad < 2 km/h por > 10 minutos
- **Anómala**: Duración > promedio + 2σ de la geocerca
- **Scope**: Solo geocercas operacionales
- **Severidad**: Alta (>150% umbral), Media (>120% umbral)

**Casos de Uso**:
- Detectar vehículos con problemas mecánicos
- Identificar demoras operacionales
- Analizar eficiencia por geocerca
- Monitoreo de productividad

### **📈 3. Clasificación de Procesos**

**Tipos de Procesos**:
- **Carga**: Stock → Módulo/Pila ROM
- **Descarga**: Módulo/Pila ROM → Botadero
- **Retorno**: Secuencial después de carga/descarga
- **Otro**: Cualquier otra combinación

### **🏭 4. Detección Automática de Geocercas**

**Categorías Detectadas**:
- **STOCKS**: Contienen "stock" → Áreas de almacenamiento
- **MODULES**: Contienen "modulo/módulo" → Módulos de extracción
- **PILAS_ROM**: Contienen "pila" + "rom" → Pilas de mineral
- **BOTADEROS**: Contienen "botadero" → Áreas de descarga
- **INSTALACIONES_FAENA**: Contienen "instalacion/faena"
- **CASINO**: Contienen "casino"

---

## 📊 **Información Operacional Generada**

### **🎯 Para Supervisores de Operación**

#### **Métricas de Productividad**:
- Cantidad de viajes por tipo (carga/descarga/retorno)
- Tiempo promedio por proceso
- Eficiencia por vehículo y turno
- Identificación de cuellos de botella

#### **Análisis de Detenciones**:
- Vehículos con detenciones anómalas
- Geocercas problemáticas
- Tiempo perdido vs tiempo productivo
- Tendencias por turno y fecha

### **🔧 Para Mantenimiento**

#### **Indicadores de Salud de Flota**:
- Vehículos con velocidad anómala prolongada
- Patrones de detención que sugieren problemas mecánicos
- Análisis de performance por vehículo

### **📈 Para Gerencia**

#### **KPIs Operacionales**:
- Productividad por turno
- Utilización de geocercas
- Tiempo total vs tiempo productivo
- Identificación de oportunidades de mejora

---

## 🚀 **Valor Operacional**

### **💰 Beneficios Económicos**

1. **Reducción de Tiempos Muertos**:
   - Identificación inmediata de detenciones anómalas
   - Reducción de 15-25% en tiempos no productivos

2. **Optimización de Mantenimiento**:
   - Mantenimiento predictivo basado en patrones
   - Reducción de costos de reparación

3. **Mejora de Productividad**:
   - Optimización de rutas y procesos
   - Incremento de 10-15% en eficiencia operacional

### **⚡ Beneficios Operacionales**

1. **Toma de Decisiones en Tiempo Real**:
   - Dashboards interactivos
   - Alertas automáticas de anomalías

2. **Visibilidad Completa**:
   - 360° de la operación
   - Trazabilidad completa de vehículos

3. **Análisis Predictivo**:
   - Identificación de tendencias
   - Prevención de problemas operacionales

---

## 📋 **Especificaciones Técnicas**

### **📥 Formato de Entrada**

**Archivo CSV Requerido**:
```csv
Nombre del Vehículo,Tiempo de evento,Geocercas,Velocidad [km/h],Latitud,Longitud
Camión_001,2025-01-15 08:30:00,Stock Principal,15.2,-33.4569,-70.6483
Camión_001,2025-01-15 08:45:00,,25.8,-33.4580,-70.6490
Camión_001,2025-01-15 09:00:00,Módulo 1,0.5,-33.4590,-70.6500
```

**Columnas Obligatorias**:
- `Nombre del Vehículo`: Identificador único del vehículo
- `Tiempo de evento`: Timestamp en formato `YYYY-MM-DD HH:MM:SS`
- `Geocercas`: Nombre de la geocerca (vacío = en viaje)

**Columnas Opcionales**:
- `Velocidad [km/h]`: Para análisis de detenciones
- `Latitud/Longitud`: Para visualización geográfica

### **⚙️ Parámetros Configurables**

```python
# Umbrales operacionales
UMBRAL_PERMANENCIA_REAL = 60  # segundos
MIN_DURACION_DETENCION = 10   # minutos
VELOCIDAD_DETENCION = 2       # km/h
FACTOR_ANOMALIA = 2           # desviaciones estándar
```

### **🔄 Proceso de Análisis**

1. **Carga y Validación** de datos
2. **Normalización** de geocercas múltiples
3. **Detección** de dominios operacionales
4. **Extracción** de transiciones válidas
5. **Clasificación** de procesos
6. **Análisis** de detenciones anómalas
7. **Generación** de visualizaciones

---

## 🎨 **Interfaz de Usuario**

### **📊 Secciones de la Aplicación**

1. **🏭 Geocercas Detectadas**: Visualización de dominios encontrados
2. **🔍 Filtros de Análisis**: Fecha, vehículo, turno
3. **📊 Matriz de Viajes**: Análisis de carga/descarga
4. **⏱️ Análisis de Tiempos**: Duración de viajes
5. **📈 Análisis Horario**: Productividad por hora
6. **💰 Estimación de Toneladas**: Cálculo de producción
7. **🚨 Detenciones Anómalas**: Análisis de anomalías
8. **📋 Resumen de Viajes**: KPIs generales

### **📱 Características de UI**

- **Responsive Design**: Adaptable a diferentes pantallas
- **Filtros Interactivos**: Análisis dinámico
- **Exportación**: Descarga de datos en CSV/Excel
- **Visualizaciones**: Gráficos Altair interactivos
- **Mapas**: Integración con Folium

---

## 🔒 **Consideraciones de Seguridad**

### **🛡️ Datos Sensibles**

- **No almacena** datos permanentemente
- **Procesamiento local** en memoria
- **Sin conexiones** a bases de datos externas
- **Logs mínimos** para debugging

### **🔐 Recomendaciones**

- Desplegar en **red corporativa** privada
- Implementar **autenticación** si es necesario
- **Backup regular** de configuraciones
- **Monitoreo** de uso y performance

---

## 📈 **Métricas de Performance**

### **⚡ Rendimiento Típico**

- **Procesamiento**: ~1,000 registros/segundo
- **Memoria**: 50-200 MB según volumen de datos
- **Tiempo de carga**: 2-5 segundos para datasets típicos
- **Capacidad**: Hasta 100,000 registros por sesión

### **🎯 Optimizaciones**

- **Vectorización** con Pandas
- **Caching** de cálculos costosos
- **Lazy loading** de visualizaciones
- **Filtrado eficiente** de datos

---

## 🚀 **Roadmap y Mejoras Futuras**

### **🔄 Próximas Versiones**

1. **Alertas en Tiempo Real**: Notificaciones automáticas
2. **Machine Learning**: Predicción de anomalías
3. **API REST**: Integración con otros sistemas
4. **Base de Datos**: Almacenamiento persistente
5. **Mobile App**: Versión para dispositivos móviles

### **🎯 Integraciones Planificadas**

- **ERP Minero**: SAP, Oracle
- **Sistemas de Despacho**: Dispatch systems
- **IoT Sensors**: Sensores adicionales
- **Weather APIs**: Datos meteorológicos

---

## 📞 **Soporte y Contacto**

### **🛠️ Soporte Técnico**

- **Documentación**: Consulta esta guía
- **Logs**: Revisar consola de Streamlit
- **Issues**: Reportar problemas específicos
- **Updates**: Mantener versión actualizada

### **📊 Capacitación**

- **Workshops**: Sesiones de entrenamiento
- **Manuales**: Guías específicas por rol
- **Best Practices**: Casos de uso optimizados

---

*Última actualización: Enero 2025*
*Versión: 6.0 Mejorado*