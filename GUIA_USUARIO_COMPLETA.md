# 📊 T-Metal BI - Guía Completa del Usuario

## 🎯 Introducción

El sistema T-Metal BI es una plataforma avanzada de Business Intelligence diseñada específicamente para operaciones mineras. Analiza datos GPS de la flota de vehículos para generar métricas operacionales, detectar patrones de productividad y optimizar procesos mineros.

## 🚀 Características Principales

### ✨ **Funcionalidades Core**
- **📊 Análisis de Transiciones**: Detección automática de movimientos entre geocercas
- **🔄 Detección de Ciclos**: Identificación de ciclos operacionales completos
- **📈 Métricas de Productividad**: Cálculo de eficiencia por vehículo y turno
- **🪨 Estimación de Toneladas**: Cálculo automático de producción (42 ton/viaje)
- **⏱️ Análisis de Tiempos de Viaje**: Medición de tiempos entre geocercas
- **🗺️ Mapeo de Zonas No Mapeadas**: Identificación de áreas operacionales no registradas

### 🔧 **Funcionalidades Avanzadas**
- **🌅🌙 Sistema de Turnos**: Análisis diferenciado día/noche (8:00-20:00 / 20:00-8:00)
- **🎯 Filtrado Inteligente**: Eliminación automática de ruido GPS
- **📋 Clasificación Automática**: Categorización inteligente de geocercas
- **🔗 Agrupación Espacial**: Clustering de zonas cercanas con radio configurable
- **💾 Exportación Completa**: Reportes detallados en Excel
- **📱 Dashboard Interactivo**: Interfaz web responsive con Streamlit

## 📥 Formato de Entrada de Datos

### 📋 **Estructura del CSV Requerida**

El sistema requiere un archivo CSV con las siguientes columnas obligatorias:

```csv
Nombre del Vehículo,Tiempo de evento,Geocercas,Velocidad [km/h],Latitud,Longitud,Hipervínculo
C-727,2024-01-15 08:30:15,Stock Central,,,-33.4569,-70.6483,https://maps.google.com/?q=-33.4569,-70.6483
C-727,2024-01-15 08:45:22,,-5.2,-33.4580,-70.6490,https://maps.google.com/?q=-33.4580,-70.6490
C-727,2024-01-15 09:15:30,Módulo 1,0.8,-33.4590,-70.6500,https://maps.google.com/?q=-33.4590,-70.6500
```

### 📊 **Descripción de Columnas**

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| **Nombre del Vehículo** | Texto | Identificador único del vehículo | `C-727`, `C-850` |
| **Tiempo de evento** | DateTime | Timestamp del registro GPS | `2024-01-15 08:30:15` |
| **Geocercas** | Texto | Nombre de la geocerca (vacío = en viaje) | `Stock Central`, `Módulo 1`, `` |
| **Velocidad [km/h]** | Numérico | Velocidad del vehículo | `15.5`, `0.0`, `-5.2` |
| **Latitud** | Numérico | Coordenada de latitud | `-33.4569` |
| **Longitud** | Numérico | Coordenada de longitud | `-70.6483` |
| **Hipervínculo** | URL | Enlace a Google Maps (opcional) | `https://maps.google.com/?q=...` |

### ⚠️ **Consideraciones Importantes**

1. **Geocercas Vacías**: Indican que el vehículo está "en viaje" entre geocercas
2. **Velocidades Negativas**: Se interpretan como vehículo detenido
3. **Timestamps**: Deben estar en formato `YYYY-MM-DD HH:MM:SS`
4. **Coordenadas**: Formato decimal (no grados/minutos/segundos)

## 🏗️ Detección Automática de Geocercas

### 🎯 **Tipos de Geocercas Detectadas**

El sistema clasifica automáticamente las geocercas según palabras clave:

#### **📦 STOCKS** (Áreas de Almacenamiento)
- **Detección**: Contienen "stock" en el nombre
- **Ejemplos**: `Stock Central`, `Stock Norte`, `STOCK-01`
- **Función**: Puntos de origen para operaciones de carga

#### **⚒️ MODULES** (Módulos de Extracción)
- **Detección**: Contienen "modulo" o "módulo"
- **Ejemplos**: `Módulo 1`, `Modulo Norte`, `MODULE-A`
- **Función**: Áreas de carga de material

#### **🪨 PILAS_ROM** (Pilas de Mineral)
- **Detección**: Contienen "pila" y "rom"
- **Ejemplos**: `Pila Rom 1`, `PILA ROM NORTE`, `Pila-Rom-Central`
- **Función**: Áreas de carga de mineral ROM

#### **🚛 BOTADEROS** (Áreas de Descarga)
- **Detección**: Contienen "botadero"
- **Ejemplos**: `Botadero Norte`, `BOTADERO-01`, `Botadero Estéril`
- **Función**: Puntos de descarga de material

#### **🏭 INSTALACIONES_FAENA** (Instalaciones No Operacionales)
- **Detección**: Contienen "instalacion" o "faena"
- **Ejemplos**: `Instalación de Faena`, `Faena Norte`
- **Función**: Áreas administrativas/apoyo (viajes = "otro")

#### **🍽️ CASINO** (Áreas de Alimentación)
- **Detección**: Contienen "casino"
- **Ejemplos**: `Casino Principal`, `CASINO MINA`
- **Función**: Áreas de alimentación (viajes = "otro")

### 🔗 **Agrupación Inteligente**

```python
GEOCERCAS_NO_OPERACIONALES = INSTALACIONES_FAENA ∪ CASINO
```

- **Propósito**: Geocercas sin función operacional directa
- **Clasificación**: Todos los viajes hacia/desde estas geocercas = "otro"

## 📊 Clasificación de Procesos

### 🎯 **Tipos de Procesos Operacionales**

#### **🔄 CARGA**
- **Definición**: Stock → Módulo/Pila ROM
- **Ejemplos**: 
  - `Stock Central → Módulo 1`
  - `Stock Norte → Pila Rom 2`
- **Función**: Carga de material en vehículo

#### **📤 DESCARGA**
- **Definición**: Módulo/Pila ROM → Botadero
- **Ejemplos**:
  - `Módulo 1 → Botadero Norte`
  - `Pila Rom 3 → Botadero Estéril`
- **Función**: Descarga de material

#### **↩️ RETORNO**
- **Definición**: Movimiento de retorno después de proceso
- **Tipos**:
  - **Retorno post-descarga**: `Botadero → Módulo/Pila ROM`
  - **Retorno post-carga**: `Módulo/Pila ROM → Stock`
- **Función**: Regreso para nuevo ciclo

#### **❓ OTRO**
- **Definición**: Cualquier otra combinación
- **Incluye**:
  - Movimientos hacia/desde geocercas no operacionales
  - Transiciones no clasificables
  - Movimientos de mantenimiento/apoyo

### 🧠 **Lógica de Clasificación con Secuencias**

El sistema utiliza **clasificación basada en secuencias** para mayor precisión:

```python
# Prioridad 1: Geocercas No Operacionales
if origen ∈ GEOCERCAS_NO_OPERACIONALES or destino ∈ GEOCERCAS_NO_OPERACIONALES:
    return "otro"

# Prioridad 2: Procesos Operacionales
if origen ∈ STOCKS and destino ∈ (MODULES ∪ PILAS_ROM):
    return "carga"

if origen ∈ (MODULES ∪ PILAS_ROM) and destino ∈ BOTADEROS:
    return "descarga"

# Prioridad 3: Retornos con Contexto
if origen ∈ BOTADEROS and destino ∈ (MODULES ∪ PILAS_ROM) and proceso_anterior == "descarga":
    return "retorno"

if origen ∈ (MODULES ∪ PILAS_ROM) and destino ∈ STOCKS and proceso_anterior == "carga":
    return "retorno"

# Por defecto
return "otro"
```

## ⏱️ Análisis de Tiempos de Viaje

### 🎯 **Funcionalidad**

Mide el tiempo que los vehículos tardan en viajar entre geocercas cuando están "en viaje" (columna Geocercas vacía).

### 📊 **Métricas Generadas**

- **Tiempo Total de Viajes**: Suma de todos los tiempos de viaje
- **Tiempo Promedio**: Duración media por viaje
- **Distribución por Vehículo**: Análisis individual por vehículo
- **Análisis por Rutas**: Tiempo promedio por combinación origen-destino

### 🔍 **Diagnóstico de Casos DESCONOCIDO**

El sistema identifica y diagnostica viajes con origen/destino desconocido:

- **Solo origen desconocido**: Viajes que terminan en geocerca conocida
- **Solo destino desconocido**: Viajes que inician en geocerca conocida
- **Ambos desconocidos**: Viajes completamente sin contexto
- **Causas comunes**: Inicio/fin de dataset, datos incompletos, filtrado GPS

## 🗺️ Análisis de Zonas No Mapeadas

### 🎯 **Propósito**

Identifica áreas donde los vehículos permanecen mucho tiempo fuera de geocercas conocidas, sugiriendo posibles geocercas no mapeadas.

### 🔧 **Parámetros Configurables**

- **Velocidad Máxima**: 0-20 km/h (default: 5 km/h)
- **Tiempo Mínimo**: 5-60 minutos (default: 10 min)
- **Radio de Agrupación**: 5-50 metros (default: 10 m)

### 🧮 **Algoritmo de Detección**

1. **Filtrado Inicial**: 
   - Registros fuera de geocercas (`Geocercas == ""`)
   - Velocidad ≤ velocidad_max (vehículo "parado")

2. **Agrupación Temporal**:
   - Registros consecutivos separados por <5 minutos
   - Duración mínima configurable

3. **Clustering Espacial**:
   - Algoritmo DBSCAN con distancia Haversine
   - Agrupación de zonas dentro del radio especificado

4. **Métricas Calculadas**:
   - Centro ponderado por duración
   - Radio aproximado del área
   - Vehículos involucrados
   - Tiempo total de permanencia

### 🗺️ **Visualización en Mapa**

- **🟢 Marcadores Verdes**: Geocercas conocidas
- **🔴 Círculos Rojos**: Zonas individuales
- **🟠 Círculos Naranjas**: Zonas agrupadas (múltiples permanencias)
- **Tamaño**: Proporcional al tiempo de permanencia

## 🔄 Detección de Ciclos Operacionales

### 📋 **Definición de Ciclo Completo**

Un ciclo operacional completo incluye:
1. **Carga**: Stock → Módulo/Pila ROM
2. **Descarga**: Módulo/Pila ROM → Botadero  
3. **Retorno**: Botadero → Módulo/Pila ROM → Stock

### 📊 **Métricas de Ciclos**

- **Duración Total**: Tiempo completo del ciclo
- **Tiempo por Fase**: Desglose por carga/descarga/retorno
- **Eficiencia**: Comparación entre vehículos
- **Frecuencia**: Ciclos por hora/turno

## 🪨 Estimación de Toneladas

### 📊 **Metodología Simplificada**

- **Valor Fijo**: 42 toneladas por viaje de producción
- **Viajes de Producción**: Clasificados como "carga" o "descarga"
- **Cálculo**: `Total Toneladas = Viajes Producción × 42`

### 📈 **Métricas Generadas**

- **Toneladas por Hora**: Producción horaria
- **Toneladas por Vehículo**: Producción individual
- **Toneladas por Turno**: Comparación día/noche
- **Toneladas Acumuladas**: Evolución temporal

## 🌅🌙 Sistema de Turnos

### ⏰ **Definición de Turnos**

- **Turno Día**: 08:00 - 20:00 (12 horas)
- **Turno Noche**: 20:00 - 08:00 (12 horas)

### 📊 **Análisis Diferenciado**

Todas las métricas se calculan por separado para cada turno:
- Transiciones por turno
- Productividad por turno
- Toneladas por turno
- Tiempos de viaje por turno

## 🎛️ Filtros y Configuración

### 📅 **Filtros Disponibles**

1. **Fecha**: Rango de fechas específico
2. **Vehículo**: Selección individual o múltiple
3. **Turno**: Día, Noche, o Ambos
4. **Geocerca Origen**: Filtro por punto de partida
5. **Geocerca Destino**: Filtro por punto de llegada

### ⚙️ **Parámetros Configurables**

- **Tiempo Mínimo de Permanencia**: 60 segundos (filtro GPS)
- **Velocidad Máxima para "Parado"**: 5 km/h
- **Radio de Agrupación Espacial**: 10 metros
- **Tiempo Mínimo de Viaje**: 30 segundos

## 📊 Dashboard y Visualizaciones

### 🏠 **Secciones del Dashboard**

#### **1. 📍 Geocercas Detectadas Automáticamente**
- Lista completa de geocercas por tipo
- Conteo por categoría
- Geocercas no clasificadas

#### **2. 🎛️ Filtros de Análisis**
- Controles interactivos en 5 columnas
- Filtrado en tiempo real
- Persistencia de selección

#### **3. 🚛 Matriz de Viajes de Producción**
- **Pestaña General**: Matriz origen-destino global
- **Pestaña por Vehículo**: Análisis individual detallado
- Conteos de carga/descarga por ruta

#### **4. ⏱️ Análisis de Tiempos de Viaje**
- Métricas detalladas por vehículo
- Diagnóstico de casos desconocidos
- Tabla de viajes con tiempos

#### **5. 📈 Producción Horaria**
- Gráfico de barras por hora
- Diferenciación por tipo de proceso
- Evolución temporal

#### **6. 🪨 Toneladas Estimadas**
- Acumulado por hora
- Distribución por vehículo
- Totales por turno

#### **7. 📋 Resumen por Tipo**
- Conteo de transiciones por proceso
- Porcentajes de distribución
- Comparación entre tipos

#### **8. 🗺️ Análisis de Zonas No Mapeadas**
- Controles de configuración
- Tabla de zonas candidatas
- Mapa interactivo con clustering
- Recomendaciones automáticas

### 📊 **Tipos de Gráficos**

- **Gráficos de Barras**: Producción horaria, conteos por tipo
- **Gráficos de Líneas**: Evolución temporal, acumulados
- **Tablas Interactivas**: Datos detallados con filtros
- **Mapas Interactivos**: Visualización espacial con Folium
- **Métricas**: KPIs destacados con st.metric

## 💾 Exportación de Datos

### 📁 **Formato Excel Completo**

El sistema genera un archivo Excel con múltiples hojas:

#### **📋 Hojas Incluidas**

1. **Transiciones**: Todos los movimientos detectados
2. **TiemposViaje**: Análisis de duración de viajes
3. **MetricasViaje**: Estadísticas por vehículo
4. **CiclosMejorados**: Ciclos operacionales completos
5. **ProduccionHoraria**: Datos de producción por hora
6. **ToneladasEstimadas**: Cálculos de tonelaje
7. **ResumenTipos**: Conteos por tipo de proceso

#### **📊 Contenido por Hoja**

- **Datos filtrados**: Según selección del usuario
- **Cálculos aplicados**: Métricas procesadas
- **Formato profesional**: Listo para reportes

## 🚀 Guía de Uso Paso a Paso

### 1. **📥 Preparación de Datos**
```bash
# Verificar formato del CSV
- Columnas obligatorias presentes
- Formato de fecha correcto
- Coordenadas en formato decimal
```

### 2. **🌐 Iniciar Aplicación**
```bash
streamlit run app6_mejorado.py
```

### 3. **📂 Cargar Datos**
- Usar el widget de carga de archivos
- Verificar que aparezcan las geocercas detectadas
- Revisar métricas iniciales

### 4. **🎛️ Configurar Filtros**
- Seleccionar rango de fechas
- Elegir vehículos de interés
- Configurar turno si es necesario

### 5. **📊 Explorar Análisis**
- Revisar matriz de viajes de producción
- Analizar tiempos de viaje
- Verificar estimaciones de toneladas

### 6. **🗺️ Identificar Zonas No Mapeadas**
- Ajustar parámetros de detección
- Revisar zonas candidatas
- Analizar recomendaciones

### 7. **💾 Exportar Resultados**
- Usar botón de descarga Excel
- Verificar todas las hojas generadas

## ⚠️ Solución de Problemas

### 🔧 **Problemas Comunes**

#### **"Sin viajes de producción detectados"**
- **Causa**: Filtros muy restrictivos o datos insuficientes
- **Solución**: Revisar filtros de fecha/vehículo, verificar clasificación de geocercas

#### **"Muchos destinos DESCONOCIDO"**
- **Causa**: Datos incompletos o filtrado GPS agresivo
- **Solución**: Revisar calidad de datos GPS, ajustar parámetros de filtrado

#### **"No se detectan geocercas"**
- **Causa**: Nombres no coinciden con patrones esperados
- **Solución**: Verificar nomenclatura de geocercas en CSV

#### **"Zonas no mapeadas irrelevantes"**
- **Causa**: Parámetros de detección muy permisivos
- **Solución**: Aumentar tiempo mínimo, reducir velocidad máxima

### 📞 **Soporte Técnico**

Para problemas adicionales:
1. Verificar logs de consola
2. Revisar formato de datos de entrada
3. Consultar documentación técnica
4. Contactar al equipo de desarrollo

## 🔄 Actualizaciones y Mantenimiento

### 📋 **Historial de Versiones**
- Consultar `CHANGELOG.md` para cambios recientes
- Revisar `requirements.txt` para dependencias actualizadas

### 🔧 **Configuración Avanzada**
- Parámetros modificables en código fuente
- Personalización de reglas de clasificación
- Ajuste de algoritmos de detección

---

## 📞 Contacto y Soporte

**Desarrollado para T-Metal**  
**Versión**: 6.0 (Mejorado)  
**Última actualización**: Enero 2024

Para soporte técnico o consultas sobre funcionalidades específicas, contactar al equipo de desarrollo.