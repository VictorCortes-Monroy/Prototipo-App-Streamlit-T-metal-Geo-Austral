# 📥 ESPECIFICACIÓN DE INPUT - T-Metal BI Operacional

## 🎯 Descripción General

El sistema T-Metal BI Operacional procesa datos GPS de flota minera exportados desde **GeoAustral** para generar métricas de productividad, producción horaria y ciclos operacionales.

## 📋 Formato de Entrada

### Archivo CSV Requerido

El sistema acepta **únicamente archivos CSV** exportados desde GeoAustral con la siguiente estructura:

```csv
Nombre del Vehículo,Tiempo de evento,Geocercas
Camión_001,2025-01-15 08:30:00,Stock Principal
Camión_001,2025-01-15 08:45:00,Módulo 1
Camión_002,2025-01-15 20:30:00,Pila Rom 1
Camión_002,2025-01-15 20:45:00,Botadero Central
```

## 🏗️ Especificación de Columnas

### 1. Nombre del Vehículo
- **Tipo**: String (texto)
- **Obligatorio**: ✅ Sí
- **Descripción**: Identificador único del vehículo
- **Ejemplos**: 
  - `"Camión_001"`
  - `"Excavadora_02"`
  - `"Cargador_03"`
- **Restricciones**: No puede estar vacío

### 2. Tiempo de evento
- **Tipo**: DateTime (fecha y hora)
- **Obligatorio**: ✅ Sí
- **Formato**: `YYYY-MM-DD HH:MM:SS`
- **Ejemplos**:
  - `"2025-01-15 08:30:00"`
  - `"2025-01-15 20:45:30"`
  - `"2025-01-16 02:15:45"`
- **Restricciones**: 
  - Debe ser una fecha válida
  - Formato 24 horas
  - Se aceptan segundos opcionales

### 3. Geocercas
- **Tipo**: String (texto)
- **Obligatorio**: ✅ Sí
- **Descripción**: Nombre de la geocerca donde se encuentra el vehículo
- **Ejemplos**:
  - `"Stock Principal"`
  - `"Módulo 1"`
  - `"Pila Rom 2"`
  - `"Botadero Central"`
- **Restricciones**: 
  - Puede estar vacío (se ignorará)
  - Se normaliza automáticamente

## 🔍 Detección Automática de Tipos de Geocerca

El sistema detecta automáticamente los tipos de geocerca basándose en palabras clave:

### Tipos Soportados

| Tipo | Palabras Clave | Ejemplos | Función Operacional |
|------|----------------|----------|-------------------|
| **STOCKS** | `"stock"` | `"Stock Principal"`, `"Stock Secundario"` | Área de almacenamiento |
| **MODULES** | `"modulo"` | `"Módulo 1"`, `"Módulo 2"`, `"Módulo 3"` | Área de procesamiento |
| **PILAS_ROM** | `"pila rom"` | `"Pila Rom 1"`, `"Pila Rom 2"`, `"Pila Rom 3"` | Área de carga adicional |
| **BOTADEROS** | `"botadero"` | `"Botadero Central"`, `"Botadero Norte"` | Área de descarga |

### Proceso de Normalización

```python
def normalizar(s: str) -> str:
    """Quita tildes y pasa a minúsculas para detección robusta."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
```

**Ejemplos de normalización:**
- `"MÓDULO 2"` → `"modulo 2"`
- `"Pila Rom 1"` → `"pila rom 1"`
- `"Stock Principal"` → `"stock principal"`

## ⚙️ Procesamiento del Input

### 1. Preparación de Datos

```python
def preparar_datos(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # Conversión de timestamps
    df["Tiempo de evento"] = pd.to_datetime(df["Tiempo de evento"], errors="coerce")
    # Eliminación de registros sin tiempo válido
    df.dropna(subset=["Tiempo de evento"], inplace=True)
    # Limpieza de nombres de geocercas
    df["Geocerca"] = df["Geocercas"].fillna("").str.strip()
    # Ordenamiento por vehículo y tiempo
    df.sort_values(["Nombre del Vehículo", "Tiempo de evento"], inplace=True)
    return df
```

### 2. Detección de Dominios

```python
def poblar_dominios(df: pd.DataFrame) -> None:
    geos = set(df["Geocerca"].unique()) - {""}
    STOCKS    = {g for g in geos if "stock"    in normalizar(g)}
    MODULES   = {g for g in geos if "modulo"   in normalizar(g)}
    BOTADEROS = {g for g in geos if "botadero" in normalizar(g)}
    PILAS_ROM = {g for g in geos if "pila rom" in normalizar(g)}
```

### 3. Extracción de Transiciones

El sistema detecta movimientos entre geocercas con las siguientes reglas:

- **Tiempo mínimo de estancia**: 60 segundos
- **Ordenamiento**: Por vehículo y tiempo cronológico
- **Filtrado**: Solo registros con geocercas válidas

## 📊 Ejemplos de Datos de Entrada

### Ejemplo 1: Datos Básicos
```csv
Nombre del Vehículo,Tiempo de evento,Geocercas
Camión_001,2025-01-15 08:30:00,Stock Principal
Camión_001,2025-01-15 08:45:00,Módulo 1
Camión_001,2025-01-15 09:15:00,Stock Principal
Camión_001,2025-01-15 09:30:00,Pila Rom 1
Camión_001,2025-01-15 10:00:00,Botadero Central
```

### Ejemplo 2: Múltiples Vehículos
```csv
Nombre del Vehículo,Tiempo de evento,Geocercas
Camión_001,2025-01-15 08:30:00,Stock Principal
Camión_001,2025-01-15 08:45:00,Módulo 1
Camión_002,2025-01-15 20:30:00,Stock Secundario
Camión_002,2025-01-15 20:45:00,Módulo 2
Camión_002,2025-01-15 21:15:00,Stock Secundario
Excavadora_01,2025-01-15 14:30:00,Pila Rom 1
Excavadora_01,2025-01-15 15:00:00,Botadero Norte
```

### Ejemplo 3: Datos con Turnos Mixtos
```csv
Nombre del Vehículo,Tiempo de evento,Geocercas
Camión_001,2025-01-15 07:30:00,Stock Principal
Camión_001,2025-01-15 08:00:00,Módulo 1
Camión_001,2025-01-15 19:30:00,Stock Principal
Camión_001,2025-01-15 20:00:00,Pila Rom 1
Camión_001,2025-01-15 21:00:00,Botadero Central
Camión_001,2025-01-16 02:30:00,Stock Principal
```

## ⚠️ Requisitos y Validaciones

### ✅ Requisitos Mínimos

1. **Formato de archivo**: CSV válido
2. **Columnas obligatorias**: 
   - `Nombre del Vehículo`
   - `Tiempo de evento`
   - `Geocercas`
3. **Datos mínimos**: Al menos 2 registros por vehículo
4. **Timestamps válidos**: Formato `YYYY-MM-DD HH:MM:SS`
5. **Geocercas válidas**: Al menos una geocerca con nombre no vacío

### 🔍 Validaciones Automáticas

| Validación | Descripción | Acción del Sistema |
|------------|-------------|-------------------|
| **Timestamps inválidos** | Fechas/horas mal formateadas | Elimina registros automáticamente |
| **Columnas faltantes** | Ausencia de columnas obligatorias | Muestra error y detiene procesamiento |
| **Geocercas vacías** | Nombres vacíos o nulos | Ignora registros en análisis |
| **Datos insuficientes** | Menos de 2 registros por vehículo | No genera transiciones |
| **Tiempo mínimo** | Estancia menor a 60 segundos | Filtra transiciones |

### ❌ Errores Comunes

#### 1. Timestamps Inválidos
```csv
# ❌ INCORRECTO
Camión_001,2025-13-45 25:70:99,Stock Principal

# ✅ CORRECTO
Camión_001,2025-01-15 08:30:00,Stock Principal
```

#### 2. Columnas Faltantes
```csv
# ❌ INCORRECTO - Falta "Tiempo de evento"
Nombre del Vehículo,Geocercas
Camión_001,Stock Principal

# ✅ CORRECTO
Nombre del Vehículo,Tiempo de evento,Geocercas
Camión_001,2025-01-15 08:30:00,Stock Principal
```

#### 3. Geocercas Vacías
```csv
# ❌ INCORRECTO - Geocerca vacía
Camión_001,2025-01-15 08:30:00,
Camión_001,2025-01-15 08:45:00,""

# ✅ CORRECTO
Camión_001,2025-01-15 08:30:00,Stock Principal
Camión_001,2025-01-15 08:45:00,Módulo 1
```

## 🎯 Resultado del Procesamiento

A partir del input válido, el sistema genera:

### 1. Transiciones Detectadas
```python
# Ejemplo de salida
{
    "Nombre del Vehículo": "Camión_001",
    "Origen": "Stock Principal",
    "Destino": "Módulo 1",
    "Tiempo_entrada": "2025-01-15 08:30:00",
    "Tiempo_salida": "2025-01-15 08:45:00",
    "Duracion_s": 900,
    "Turno": "dia",
    "Proceso": "carga"
}
```

### 2. Procesos Clasificados
- **Carga**: Stock → Módulo/Pila ROM
- **Descarga**: Módulo/Pila ROM → Botadero
- **Retorno**: Módulo/Pila ROM → Stock
- **Otros**: Cualquier otra combinación

### 3. Métricas Generadas
- **Producción horaria**: Viajes por hora
- **Productividad**: % horas de carga vs activas
- **Ciclos completos**: Stock → Módulo → Stock
- **Toneladas estimadas**: Por viaje de producción

## 📁 Archivo de Prueba

El sistema incluye `datos_prueba.csv` con ejemplos de todos los tipos de geocercas y casos de uso para validar el funcionamiento.

## 🚀 Instrucciones de Uso

1. **Preparar datos**: Exportar desde GeoAustral en formato CSV
2. **Verificar formato**: Asegurar columnas obligatorias presentes
3. **Cargar archivo**: Usar el uploader de la aplicación
4. **Aplicar filtros**: Seleccionar rango de fechas y vehículos
5. **Analizar resultados**: Revisar métricas y visualizaciones

## 📞 Soporte Técnico

Para problemas con el formato de entrada:
- Verificar que el CSV tenga las 3 columnas obligatorias
- Validar formato de timestamps
- Asegurar que haya al menos 2 registros por vehículo
- Revisar que las geocercas contengan nombres válidos

---

**Versión**: 2.0.0  
**Fecha**: 2025-01-15  
**Sistema**: T-Metal BI Operacional 