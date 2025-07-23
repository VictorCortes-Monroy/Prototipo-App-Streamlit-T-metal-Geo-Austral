# 📋 Checklist de Pruebas Manuales - T-Metal BI Operacional

## 🎯 **Objetivo**
Validar todas las funcionalidades de la aplicación `app5.py` antes de llevarla a producción.

## 🚀 **Preparación**
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Ejecutar aplicación: `streamlit run app5.py`
- [ ] Abrir navegador en: `http://localhost:8501`
- [ ] Tener archivo `datos_prueba.csv` listo

---

## 📊 **1. Pruebas de Carga de Datos**

### **1.1 Carga de Archivo CSV**
- [ ] **Cargar archivo válido**: Subir `datos_prueba.csv`
- [ ] **Verificar carga exitosa**: Debe mostrar datos sin errores
- [ ] **Verificar columnas**: Debe detectar "Nombre del Vehículo", "Tiempo de evento", "Geocercas"
- [ ] **Verificar fechas**: Debe mostrar rango de fechas disponible

### **1.2 Detección de Geocercas**
- [ ] **Stocks detectados**: "Stock Principal", "Stock Secundario"
- [ ] **Módulos detectados**: "Módulo 1", "Módulo 2", "Módulo 3"
- [ ] **Pilas ROM detectadas**: "Pila Rom 1", "Pila Rom 2", "Pila Rom 3"
- [ ] **Botaderos detectados**: "Botadero Central", "Botadero Norte"

---

## 🔍 **2. Pruebas de Filtros**

### **2.1 Filtro por Fechas**
- [ ] **Seleccionar rango completo**: Verificar que muestra todos los datos
- [ ] **Seleccionar fecha específica**: Verificar que filtra correctamente
- [ ] **Seleccionar rango parcial**: Verificar que filtra fechas intermedias
- [ ] **Cambiar fechas dinámicamente**: Verificar que actualiza métricas

### **2.2 Filtro por Vehículo**
- [ ] **Seleccionar "Todos"**: Verificar que muestra todos los vehículos
- [ ] **Seleccionar vehículo específico**: Verificar que filtra correctamente
- [ ] **Cambiar vehículo**: Verificar que actualiza métricas
- [ ] **Combinar con filtro de fechas**: Verificar funcionamiento conjunto

### **2.3 Filtro por Turno**
- [ ] **Seleccionar "Todos"**: Verificar que muestra datos de ambos turnos
- [ ] **Seleccionar "Día"**: Verificar que filtra solo turno día (8:00-20:00)
- [ ] **Seleccionar "Noche"**: Verificar que filtra solo turno noche (20:00-8:00)
- [ ] **Combinar con otros filtros**: Verificar funcionamiento conjunto

---

## 📈 **3. Pruebas de Visualizaciones**

### **3.1 Producción Horaria**
- [ ] **Gráfico de carga**: Verificar que muestra viajes de carga por hora
- [ ] **Tooltips**: Verificar que muestra información al pasar el mouse
- [ ] **Escala temporal**: Verificar que el eje X muestra fechas correctas
- [ ] **Datos filtrados**: Verificar que responde a filtros aplicados

### **3.2 Producción por Turno**
- [ ] **Gráfico de turnos**: Verificar que diferencia día/noche con colores
- [ ] **Estadísticas por turno**: Verificar métricas separadas
- [ ] **Resumen comparativo**: Verificar tabla de comparación
- [ ] **Colores diferenciados**: Día (rojo) vs Noche (turquesa)

### **3.3 Conteo Global**
- [ ] **Tabla de viajes**: Verificar conteo por tipo de proceso
- [ ] **Procesos mostrados**: Carga, retorno, descarga, otro
- [ ] **Totales correctos**: Verificar que suman correctamente
- [ ] **Actualización con filtros**: Verificar que cambia al filtrar

---

## 🔄 **4. Pruebas de Ciclos y Productividad**

### **4.1 Ciclos Completos**
- [ ] **Tabla de ciclos**: Verificar que muestra ciclos por vehículo
- [ ] **Ordenamiento**: Verificar que ordena por cantidad de ciclos
- [ ] **Ciclos detectados**: Verificar que detecta Stock→Módulo/Pila ROM→Stock
- [ ] **Conteo correcto**: Verificar números de ciclos

### **4.2 Productividad**
- [ ] **Productividad promedio**: Verificar cálculo de % horas carga vs activas
- [ ] **Tabla por vehículo**: Verificar productividad individual
- [ ] **Gráfico de barras**: Verificar visualización de productividad
- [ ] **Ordenamiento**: Verificar que ordena por productividad

### **4.3 Métricas por Turno**
- [ ] **Turno Día**: Verificar métricas específicas
- [ ] **Turno Noche**: Verificar métricas específicas
- [ ] **Fechas mostradas**: Verificar que indica fechas involucradas
- [ ] **Productividad por turno**: Verificar cálculos separados

---

## 🪨 **5. Pruebas de Toneladas**

### **5.1 Estimación de Toneladas**
- [ ] **Distribución normal**: Verificar que usa N(42t, σ=3t)
- [ ] **Gráfico de barras**: Verificar visualización por hora
- [ ] **Tooltips**: Verificar información de toneladas
- [ ] **Acumulación**: Verificar que suma correctamente

### **5.2 Filtros en Toneladas**
- [ ] **Filtro por fecha**: Verificar que responde a fechas
- [ ] **Filtro por vehículo**: Verificar que responde a vehículos
- [ ] **Filtro por turno**: Verificar que responde a turnos

---

## 📋 **6. Pruebas de Detalles**

### **6.1 Expander de Transiciones**
- [ ] **Abrir expander**: Verificar que muestra tabla de transiciones
- [ ] **Columnas mostradas**: Origen, Destino, Tiempos, Duración, Turno
- [ ] **Datos correctos**: Verificar que muestra transiciones reales
- [ ] **Filtros aplicados**: Verificar que responde a filtros

### **6.2 Exportación Excel**
- [ ] **Botón de descarga**: Verificar que aparece
- [ ] **Descargar archivo**: Verificar que genera archivo .xlsx
- [ ] **Hojas incluidas**: Transiciones, ViajesHora, Ciclos, Productividad
- [ ] **Datos correctos**: Verificar que exporta datos filtrados

---

## 🧪 **7. Pruebas de Casos Especiales**

### **7.1 Datos Vacíos**
- [ ] **Sin transiciones**: Verificar mensaje de advertencia
- [ ] **Sin datos de carga**: Verificar mensaje informativo
- [ ] **Sin productividad**: Verificar manejo de datos faltantes
- [ ] **Sin ciclos**: Verificar tabla vacía

### **7.2 Datos Extremos**
- [ ] **Muchos vehículos**: Verificar rendimiento
- [ ] **Período largo**: Verificar manejo de fechas extensas
- [ ] **Geocercas nuevas**: Verificar detección automática
- [ ] **Datos inconsistentes**: Verificar manejo de errores

### **7.3 Interacciones**
- [ ] **Cambios rápidos de filtros**: Verificar estabilidad
- [ ] **Múltiples filtros**: Verificar funcionamiento conjunto
- [ ] **Navegación**: Verificar que no se pierden datos
- [ ] **Responsive**: Verificar en diferentes tamaños de pantalla

---

## 🔧 **8. Pruebas de Rendimiento**

### **8.1 Tiempo de Respuesta**
- [ ] **Carga inicial**: < 5 segundos
- [ ] **Cambio de filtros**: < 2 segundos
- [ ] **Generación de gráficos**: < 3 segundos
- [ ] **Exportación Excel**: < 10 segundos

### **8.2 Uso de Memoria**
- [ ] **Datos grandes**: Verificar que no consume excesiva memoria
- [ ] **Múltiples sesiones**: Verificar estabilidad
- [ ] **Limpieza de datos**: Verificar que libera memoria

---

## ✅ **9. Checklist Final**

### **9.1 Funcionalidades Principales**
- [ ] ✅ Carga de datos CSV
- [ ] ✅ Detección automática de geocercas
- [ ] ✅ Filtros (fecha, vehículo, turno)
- [ ] ✅ Visualizaciones (gráficos, tablas)
- [ ] ✅ Métricas de productividad
- [ ] ✅ Detección de ciclos
- [ ] ✅ Estimación de toneladas
- [ ] ✅ Exportación a Excel

### **9.2 Integración de Pilas ROM**
- [ ] ✅ Detección automática de "Pila Rom 1", "Pila Rom 2", "Pila Rom 3"
- [ ] ✅ Clasificación correcta en procesos de carga
- [ ] ✅ Inclusión en ciclos completos
- [ ] ✅ Métricas incluyen pilas ROM

### **9.3 Funcionalidades de Turnos**
- [ ] ✅ Filtro por turno día/noche
- [ ] ✅ Métricas separadas por turno
- [ ] ✅ Visualizaciones diferenciadas
- [ ] ✅ Información de fechas por turno

### **9.4 Calidad del Código**
- [ ] ✅ Pruebas automatizadas pasan
- [ ] ✅ Sin errores de sintaxis
- [ ] ✅ Manejo de errores implementado
- [ ] ✅ Documentación actualizada

---

## 🚀 **10. Listo para Producción**

### **Criterios de Aprobación**
- [ ] **Todas las pruebas pasan**: ✅
- [ ] **Funcionalidades validadas**: ✅
- [ ] **Rendimiento aceptable**: ✅
- [ ] **Documentación completa**: ✅
- [ ] **Datos de prueba verificados**: ✅

### **Deployment**
- [ ] **Backup del código actual**
- [ ] **Documentación de cambios**
- [ ] **Plan de rollback**
- [ ] **Monitoreo post-deployment**

---

## 📝 **Notas de Pruebas**

**Fecha de pruebas**: _______________
**Probador**: _______________
**Versión**: app5.py con Pilas ROM y Turnos

**Observaciones**:
- 

**Problemas encontrados**:
- 

**Acciones correctivas**:
- 

**Estado final**: ⏳ En progreso / ✅ Aprobado / ❌ Rechazado 