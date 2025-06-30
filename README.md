# ⛏️ T-Metal - BI Operacional

## Descripción

Sistema de Business Intelligence operacional para T-Metal que analiza datos GPS de flota minera para generar métricas de productividad, producción horaria y ciclos operacionales.

## 🚀 Características Principales

- **Producción Horaria**: Análisis de viajes de carga por hora
- **Conteo de Viajes**: Estadísticas por tipo de proceso (carga, retorno, descarga)
- **Ciclos Completos**: Detección automática de ciclos Stock→Módulo→Stock
- **Productividad**: Cálculo de % horas de carga vs horas activas por vehículo
- **Toneladas Estimadas**: Estimación de toneladas transportadas (distribución normal)
- **Exportación Excel**: Generación de reportes en formato Excel

## 📋 Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## 🛠️ Instalación

1. **Clonar el repositorio**:
```bash
git clone https://github.com/tu-usuario/t-metal-bi.git
cd t-metal-bi
```

2. **Crear entorno virtual**:
```bash
python -m venv env
```

3. **Activar entorno virtual**:
```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

## 🚀 Uso

1. **Ejecutar la aplicación**:
```bash
streamlit run app5.py
```

2. **Acceder a la aplicación**:
   - Abrir navegador en `http://localhost:8501`

3. **Cargar datos**:
   - Subir archivo CSV exportado desde GeoAustral
   - Seleccionar rango de fechas
   - Filtrar por vehículo específico (opcional)

## 📊 Funcionalidades

### Dashboard Principal
- **Gráfico de Producción Horaria**: Muestra viajes de carga por hora
- **Conteo Global**: Estadísticas totales de viajes por tipo
- **Ciclos Completos**: Número de ciclos por vehículo
- **Productividad**: Métricas de eficiencia operacional

### Análisis de Datos
- **Transiciones**: Detección automática de movimientos entre geocercas
- **Clasificación**: Categorización automática de procesos
- **Métricas**: Cálculo de horas activas y productividad

### Exportación
- **Reporte Excel**: Descarga de datos procesados en múltiples hojas
- **Hojas incluidas**:
  - Transiciones
  - Viajes por Hora
  - Ciclos
  - Productividad

## 🔧 Configuración

### Parámetros Globales
```python
MIN_ESTANCIA_S = 60          # Tiempo mínimo de estancia (segundos)
SHIFT_DAY_START = time(8,0)  # Inicio turno día
SHIFT_NIGHT_START = time(20,0) # Inicio turno noche
```

### Dominios Automáticos
El sistema detecta automáticamente:
- **STOCKS**: Geocercas que contienen "stock"
- **MODULES**: Geocercas que contienen "modulo"
- **BOTADEROS**: Geocercas que contienen "botadero"

## 📁 Estructura del Proyecto

```
t-metal-bi/
├── app5.py              # Aplicación principal
├── requirements.txt     # Dependencias
├── README.md           # Documentación
└── .gitignore          # Archivos a ignorar
```

## 🔍 Procesamiento de Datos

### 1. Preparación
- Conversión de timestamps
- Limpieza de datos GPS
- Normalización de nombres de geocercas

### 2. Extracción de Transiciones
- Detección de cambios entre geocercas
- Filtrado por tiempo mínimo de estancia
- Clasificación por turnos

### 3. Análisis Operacional
- Clasificación de procesos (carga/retorno/descarga)
- Detección de ciclos completos
- Cálculo de métricas de productividad

### 4. Visualización
- Gráficos interactivos con Altair
- Tablas de resumen
- Métricas en tiempo real

## 📈 Métricas Calculadas

### Productividad
```
Productividad = (Horas de Carga / Horas Activas) × 100
```

### Toneladas Estimadas
- Distribución normal: N(42 ton, σ=3 ton)
- Estimación por viaje de carga
- Acumulación horaria

### Ciclos Operacionales
- Detección de secuencias: Stock → Módulo → Stock
- Conteo por vehículo
- Análisis de eficiencia

## 🐛 Solución de Problemas

### Error: "No se encontraron transiciones válidas"
- Verificar que el CSV contenga datos de geocercas
- Revisar formato de timestamps
- Ajustar filtros de fecha

### Error: "Sin registros de carga"
- Verificar nombres de geocercas
- Revisar clasificación automática
- Ajustar parámetros de detección

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para nueva funcionalidad
3. Commit los cambios
4. Push a la rama
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Contacto

- **Desarrollador**: [Tu Nombre]
- **Email**: [tu-email@ejemplo.com]
- **Proyecto**: [URL del repositorio]

## 🔄 Historial de Versiones

### v1.0.0 (2025-01-27)
- Versión inicial
- Dashboard operacional completo
- Exportación a Excel
- Métricas de productividad 