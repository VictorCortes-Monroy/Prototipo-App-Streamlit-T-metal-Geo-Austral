# ⛏️ T-Metal - BI Operacional

## Descripción

Sistema de Business Intelligence operacional para T-Metal que analiza datos GPS de flota minera para generar métricas de productividad, producción horaria y ciclos operacionales.

## 🚀 Características Principales

- **🌅🌙 Sistema de Turnos**: Filtros y métricas diferenciadas por turno día/noche
- **🏗️ Soporte Pilas ROM**: Detección automática de Pila Rom 1, 2, 3 como áreas de carga
- **📊 Producción Mejorada**: Análisis de viajes de carga Y descarga como producción
- **📈 Visualizaciones Avanzadas**: Gráficos combinados con colores diferenciados
- **📋 Conteo Detallado**: Estadísticas completas por tipo de viaje con porcentajes
- **🔄 Ciclos Completos**: Detección automática de ciclos Stock→Módulo/Pila ROM→Stock
- **🚀 Productividad**: Cálculo de % horas de carga vs horas activas por vehículo
- **🪨 Toneladas Estimadas**: Estimación de toneladas por viaje de producción
- **💾 Exportación Excel**: Generación de reportes completos en formato Excel

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
- **PILAS_ROM**: Geocercas que contienen "pila rom" (Pila Rom 1, 2, 3)
- **BOTADEROS**: Geocercas que contienen "botadero"
- **INSTALACIONES_FAENA**: Geocercas que contienen "instalacion" o "faena"
- **CASINO**: Geocercas que contienen "casino"
- **GEOCERCAS_NO_OPERACIONALES**: Incluye Instalaciones de Faena y Casino (viajes clasificados como "otro")

## 📁 Estructura del Proyecto

```
t-metal-bi/
├── app5.py                    # Aplicación principal
├── requirements.txt           # Dependencias
├── test_app5.py              # Script de pruebas automatizadas
├── datos_prueba.csv          # Datos de prueba
├── CHECKLIST_PRUEBAS.md      # Checklist de pruebas manuales
├── CHANGELOG.md              # Historial de cambios
├── README.md                 # Documentación
└── .gitignore                # Archivos a ignorar
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

- **Desarrollador**: Victor Cortes-Monroy  
- **Email**: v.cortesmonroy@tmetal.cl  
- **Proyecto**: [URL del repositorio]

## 🔄 Historial de Versiones

### v2.0.0 (2025-07-23)
- 🌅🌙 Sistema de turnos día/noche con filtros y métricas diferenciadas
- 🏗️ Integración completa de Pilas ROM (Pila Rom 1, 2, 3)
- 📊 Concepto de producción ampliado (carga + descarga)
- 📈 Visualizaciones mejoradas con colores diferenciados
- 📋 Conteo detallado de viajes con porcentajes
- 🧪 Sistema completo de pruebas automatizadas
- 📚 Documentación exhaustiva y checklist de pruebas

### v1.0.0 (2025-06-25)
- Versión inicial
- Dashboard operacional completo
- Exportación a Excel

- Métricas de productividad 
