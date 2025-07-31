# 📋 Documentación Técnica - T-Metal BI Operacional

## Arquitectura del Sistema

### Estructura del Código

El sistema está organizado en 6 módulos principales:

1. **Parámetros Globales** - Configuración del sistema
2. **Utilidades** - Funciones auxiliares
3. **Extracción de Transiciones** - Procesamiento de datos GPS
4. **Clasificación de Proceso** - Categorización de operaciones
5. **Detección de Ciclos** - Análisis de secuencias operacionales
6. **Interfaz Streamlit** - Dashboard y visualización

## Análisis Detallado por Módulo

### 1. Parámetros Globales

```python
MIN_ESTANCIA_S      = 60          # Tiempo mínimo en geocerca (segundos)
SHIFT_DAY_START     = time(8, 0)  # Inicio turno día
SHIFT_NIGHT_START   = time(20, 0) # Inicio turno noche

# Dominios dinámicos detectados automáticamente
STOCKS: set[str]    = set()       # Geocercas de stock
MODULES: set[str]   = set()       # Geocercas de módulos
BOTADEROS: set[str] = set()       # Geocercas de botaderos
```

### 2. Funciones de Utilidad

#### `turno(ts: pd.Timestamp) -> str`
- **Propósito**: Determina el turno (día/noche) basado en la hora
- **Lógica**: Día: 08:00-20:00, Noche: 20:00-08:00
- **Retorna**: "dia" o "noche"

#### `normalizar(s: str) -> str`
- **Propósito**: Normaliza texto para detección robusta de geocercas
- **Proceso**: 
  - Elimina tildes y caracteres especiales
  - Convierte a minúsculas
  - Codifica/decodifica ASCII
- **Uso**: Detección automática de tipos de geocerca

#### `preparar_datos(df_raw: pd.DataFrame) -> pd.DataFrame`
- **Propósito**: Limpieza y preparación inicial de datos
- **Procesos**:
  - Conversión de timestamps
  - Eliminación de registros sin tiempo
  - Limpieza de nombres de geocercas
  - Ordenamiento por vehículo y tiempo

#### `poblar_dominios(df: pd.DataFrame) -> None`
- **Propósito**: Detección automática de tipos de geocerca
- **Algoritmo**:
  - Extrae geocercas únicas
  - Busca palabras clave en nombres normalizados
  - Clasifica en STOCKS, MODULES, BOTADEROS, PILAS_ROM, INSTALACIONES_FAENA, CASINO
  - Agrupa INSTALACIONES_FAENA y CASINO como GEOCERCAS_NO_OPERACIONALES

### 3. Extracción de Transiciones

#### `extraer_transiciones(df: pd.DataFrame) -> pd.DataFrame`
- **Propósito**: Detecta movimientos entre geocercas
- **Algoritmo**:
  1. Agrupa por vehículo
  2. Filtra registros con geocercas válidas
  3. Calcula siguiente geocerca y tiempo
  4. Identifica cambios de geocerca
  5. Filtra por tiempo mínimo de estancia
  6. Calcula duración de transición

**Campos de salida**:
- `Nombre del Vehículo`: Identificador del vehículo
- `Origen`: Geocerca de origen
- `Destino`: Geocerca de destino
- `Tiempo_entrada`: Timestamp de entrada
- `Tiempo_salida`: Timestamp de salida
- `Duracion_s`: Duración en segundos
- `Turno`: Turno (día/noche)

### 4. Clasificación de Procesos

#### `clasificar_proceso(row: pd.Series) -> str`
- **Propósito**: Categoriza transiciones en tipos de proceso
- **Clasificaciones**:
  - `"carga"`: Stock → Módulo/Pila ROM
  - `"descarga"`: Módulo/Pila ROM → Botadero
  - `"retorno"`: Botadero → Módulo/Pila ROM (después de descarga) o Módulo/Pila ROM → Stock (después de carga)
  - `"otro"`: Cualquier otra combinación, incluyendo movimientos hacia/desde Instalaciones de Faena o Casino

### 5. Detección de Ciclos

#### `detectar_ciclos(trans: pd.DataFrame) -> pd.DataFrame`
- **Propósito**: Identifica ciclos completos Stock→Módulo→Stock
- **Algoritmo**:
  1. Clasifica todas las transiciones
  2. Identifica secuencias carga→retorno consecutivas
  3. Asigna ID único a cada ciclo
- **Retorna**: DataFrame con ciclos detectados

### 6. Construcción de Métricas

#### `construir_metricas(trans: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]`
- **Propósito**: Genera métricas agregadas y productividad
- **Salidas**:
  1. **Viajes por Hora**: Conteo de transiciones por hora y tipo
  2. **Productividad**: Horas de carga vs horas activas por vehículo

**Cálculo de Productividad**:
```python
Productividad = (Horas de Carga / Horas Activas) × 100
```

## Flujo de Datos

```
CSV Input → Preparación → Transiciones → Clasificación → Ciclos → Métricas → Dashboard
```

### 1. Entrada de Datos
- **Formato**: CSV exportado desde GeoAustral
- **Campos requeridos**:
  - `Tiempo de evento`: Timestamp
  - `Nombre del Vehículo`: Identificador
  - `Geocercas`: Nombre de geocerca

### 2. Procesamiento
- **Limpieza**: Eliminación de datos inválidos
- **Normalización**: Estandarización de nombres
- **Detección**: Identificación automática de dominios

### 3. Análisis
- **Transiciones**: Movimientos entre geocercas
- **Clasificación**: Categorización de procesos
- **Ciclos**: Secuencias operacionales completas

### 4. Métricas
- **Producción**: Viajes por hora
- **Productividad**: Eficiencia operacional
- **Toneladas**: Estimación de carga transportada

## Algoritmos Clave

### Detección de Geocercas
```python
def detectar_geocercas(nombre: str) -> str:
    nombre_norm = normalizar(nombre)
    if "stock" in nombre_norm:
        return "STOCK"
    elif "modulo" in nombre_norm:
        return "MODULO"
    elif "botadero" in nombre_norm:
        return "BOTADERO"
    return "OTRO"
```

### Estimación de Toneladas
```python
# Promedio fijo de 42 toneladas por viaje de producción
toneladas = 42.0
```

### Cálculo de Productividad
```python
# Horas activas = suma de duraciones de todas las transiciones
# Horas de carga = suma de duraciones de transiciones de carga
productividad = (horas_carga / horas_activas) * 100
```

## Optimizaciones Implementadas

### 1. Procesamiento por Lotes
- Agrupación por vehículo para procesamiento eficiente
- Uso de operaciones vectorizadas de pandas

### 2. Filtrado Temprano
- Eliminación de registros inválidos en la preparación
- Filtrado por tiempo mínimo antes del análisis

### 3. Cálculos Incrementales
- Reutilización de transiciones clasificadas
- Cálculo de métricas en una sola pasada

## Consideraciones de Rendimiento

### Complejidad Temporal
- **Preparación**: O(n log n) - ordenamiento
- **Transiciones**: O(n) - una pasada por registro
- **Clasificación**: O(n) - aplicación de función
- **Ciclos**: O(n log n) - ordenamiento + detección
- **Métricas**: O(n) - agregaciones

### Optimizaciones de Memoria
- Uso de tipos de datos apropiados
- Eliminación de copias innecesarias
- Limpieza de datos intermedios

## Manejo de Errores

### Validaciones Implementadas
1. **Datos de entrada**:
   - Verificación de campos requeridos
   - Validación de formatos de timestamp
   - Manejo de valores nulos

2. **Procesamiento**:
   - Verificación de DataFrames vacíos
   - Manejo de divisiones por cero
   - Validación de rangos de datos

3. **Salida**:
   - Verificación de datos antes de visualización
   - Manejo de casos sin datos
   - Mensajes informativos al usuario

## Extensiones Futuras

### Funcionalidades Propuestas
1. **Análisis de Tendencias**: Series temporales
2. **Alertas**: Notificaciones de anomalías
3. **Reportes Automáticos**: Generación programada
4. **Integración con APIs**: Conexión directa con sistemas
5. **Machine Learning**: Predicción de productividad

### Mejoras Técnicas
1. **Base de Datos**: Persistencia de datos históricos
2. **Caché**: Optimización de consultas repetidas
3. **Paralelización**: Procesamiento multi-thread
4. **API REST**: Interfaz programática
5. **Docker**: Containerización del sistema 