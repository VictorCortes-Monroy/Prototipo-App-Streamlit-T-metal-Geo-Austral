# 👥 **GUÍA DE USUARIO - T-Metal BI Operacional**
## *Aplicación Web para Análisis de Flota Minera*

---

## 🚀 **Acceso a la Aplicación**

### **🌐 URL de Acceso**
```
https://tmetal-bi-operacional.streamlit.app
```

### **💻 Requisitos del Sistema**
- **Navegador**: Chrome, Firefox, Safari, Edge (versiones recientes)
- **Conexión**: Internet estable
- **Resolución**: Mínimo 1280x720 (recomendado 1920x1080)
- **Archivos**: Capacidad de subir archivos CSV hasta 200MB

---

## 📋 **Preparación de Datos**

### **📂 Formato de Archivo Requerido**

La aplicación acepta **únicamente archivos CSV** exportados desde GeoAustral con esta estructura:

```csv
Nombre del Vehículo,Tiempo de evento,Geocercas,Velocidad [km/h],Latitud,Longitud
C-727,2024-01-15 08:30:15,Stock Central,15.2,-33.4569,-70.6483
C-727,2024-01-15 08:45:22,,25.8,-33.4580,-70.6490
C-727,2024-01-15 09:15:30,Módulo 1,0.8,-33.4590,-70.6500
```

### **✅ Lista de Verificación Pre-Carga**

- [ ] Archivo en formato `.csv`
- [ ] Columnas obligatorias presentes
- [ ] Fechas en formato `YYYY-MM-DD HH:MM:SS`
- [ ] Nombres de vehículos consistentes
- [ ] Tamaño de archivo < 200MB

---

## 🎯 **Guía Paso a Paso**

### **1️⃣ Carga de Datos**

1. **Accede** a la aplicación web
2. **Arrastra** tu archivo CSV o **haz clic** en "Browse files"
3. **Espera** la confirmación de carga exitosa
4. **Revisa** el mensaje de geocercas detectadas

### **2️⃣ Verificación de Geocercas**

**¿Qué verás?**
- ✅ **Mensaje verde**: "Todas las geocercas fueron clasificadas correctamente"
- ⚠️ **Mensaje amarillo**: Lista de geocercas no clasificadas

**Si hay geocercas no clasificadas:**
- Revisa que los nombres coincidan con tus geocercas operacionales
- La aplicación normaliza automáticamente variaciones menores
- Las rutas y caminos se excluyen automáticamente

### **3️⃣ Configuración de Filtros**

#### **📅 Filtro de Fecha**
- **Selecciona** el rango de fechas a analizar
- **Por defecto**: Analiza todo el período disponible
- **Tip**: Para análisis diarios, selecciona el mismo día de inicio y fin

#### **🚛 Filtro de Vehículo**
- **"Todos"**: Análisis de toda la flota
- **Vehículo específico**: Análisis detallado individual
- **Uso**: Selecciona vehículo específico para investigar anomalías

#### **🌅 Filtro de Turno**
- **"Todos"**: Análisis 24/7
- **"Día"**: 08:00 - 19:59
- **"Noche"**: 20:00 - 07:59 (día siguiente)

---

## 📊 **Interpretación de Resultados**

### **🏭 Sección: Geocercas Detectadas**

#### **📦 Stocks (Áreas de Almacenamiento)**
- **Qué son**: Puntos de origen para operaciones de carga
- **Ejemplos**: "Stock Central", "Stock Norte"
- **Uso operacional**: Monitorear disponibilidad de material

#### **⚒️ Modules (Módulos de Extracción)**
- **Qué son**: Áreas de carga de material
- **Ejemplos**: "Módulo 1", "Modulo Norte"
- **Uso operacional**: Controlar eficiencia de carga

#### **🪨 Pilas ROM (Pilas de Mineral)**
- **Qué son**: Áreas de carga de mineral ROM
- **Ejemplos**: "Pila Rom 1", "Pila ROM Central"
- **Uso operacional**: Gestionar inventario de mineral

#### **🚛 Botaderos (Áreas de Descarga)**
- **Qué son**: Puntos finales de descarga
- **Ejemplos**: "Botadero Central", "Botadero Norte"
- **Uso operacional**: Controlar capacidad y distribución

### **📊 Sección: Matriz de Viajes**

#### **🔢 Interpretación de Números**
- **Cada celda**: Cantidad de viajes entre origen → destino
- **Colores**: Intensidad = Frecuencia de viajes
- **Patrones esperados**:
  - Stock → Módulo (Carga)
  - Módulo → Botadero (Descarga)
  - Botadero → Módulo (Retorno)

#### **🚨 Señales de Alerta**
- **Números muy bajos**: Posible subutilización
- **Números muy altos**: Posible sobrecarga
- **Patrones irregulares**: Investigar causas

### **🚨 Sección: Detenciones Anómalas**

#### **🎯 Criterios de Detección**
- **Detención**: Velocidad < 2 km/h por > 10 minutos
- **Anómala**: Duración > promedio + 2σ de la geocerca
- **Severidad Alta**: > 150% del tiempo normal
- **Severidad Media**: > 120% del tiempo normal

#### **📋 Tab: Detalle de Detenciones**
**Columnas importantes:**
- **Vehículo**: Identifica el equipo afectado
- **Geocerca**: Ubicación del problema
- **Duración Total**: Tiempo total de la detención
- **Exceso**: Tiempo por encima de lo normal
- **Severidad**: Criticidad del problema

#### **👷 Tab: Por Vehículo**
**Uso operacional:**
- Identificar vehículos problemáticos
- Programar mantenimiento preventivo
- Reasignar equipos si es necesario

#### **🏭 Tab: Por Geocerca**
**Uso operacional:**
- Identificar cuellos de botella operacionales
- Optimizar procesos en ubicaciones específicas
- Redistribuir carga de trabajo

#### **📈 Tab: Gráficos**
- **Distribución por Severidad**: Visión general del problema
- **Duración vs Exceso**: Identificar outliers
- **Timeline**: Patrones temporales de detenciones

---

## 🎯 **Casos de Uso por Rol**

### **👨‍💼 Supervisor de Turno**

#### **🌅 Análisis Diario (Al inicio del turno)**
1. **Carga** datos del turno anterior
2. **Revisa** sección de Detenciones Anómalas
3. **Identifica** vehículos con problemas
4. **Toma acción**: Mantenimiento o reasignación

#### **📊 Monitoreo en Tiempo Real**
1. **Actualiza** datos cada 2-4 horas
2. **Monitorea** matriz de viajes para patrones
3. **Alerta** a mantenimiento si detecta anomalías

### **🔧 Jefe de Mantenimiento**

#### **📈 Análisis Semanal**
1. **Carga** datos de la semana completa
2. **Filtra** por vehículo individual
3. **Analiza** tendencias de detenciones
4. **Programa** mantenimiento preventivo

#### **🚨 Investigación de Fallas**
1. **Selecciona** vehículo específico
2. **Revisa** tab "Timeline" para patrones
3. **Correlaciona** con reportes de operadores
4. **Documenta** hallazgos para seguimiento

### **📊 Analista de Productividad**

#### **📈 Reportes Mensuales**
1. **Carga** datos del mes completo
2. **Analiza** sección "Resumen de Viajes"
3. **Compara** productividad por turno
4. **Genera** KPIs para gerencia

#### **🎯 Optimización de Procesos**
1. **Identifica** geocercas con más detenciones
2. **Analiza** patrones por hora del día
3. **Propone** mejoras operacionales
4. **Mide** impacto de cambios implementados

### **👔 Gerente de Operaciones**

#### **📊 Dashboard Ejecutivo**
1. **Revisa** métricas principales semanalmente
2. **Foca** en tendencias y excepciones
3. **Toma decisiones** basadas en datos
4. **Comunica** resultados a stakeholders

---

## 🔄 **Flujo de Trabajo Recomendado**

### **📅 Rutina Diaria**
```
08:00 - Carga datos turno noche
08:15 - Revisa detenciones anómalas
08:30 - Briefing con supervisores
09:00 - Acciones correctivas
```

### **📊 Rutina Semanal**
```
Lunes - Análisis semanal completo
Martes - Seguimiento de acciones
Miércoles - Revisión de tendencias
Jueves - Planificación de mantenimiento
Viernes - Reporte a gerencia
```

### **📈 Rutina Mensual**
```
Semana 1 - Análisis de productividad
Semana 2 - Identificación de mejoras
Semana 3 - Implementación de cambios
Semana 4 - Medición de resultados
```

---

## ⚠️ **Troubleshooting**

### **❌ Problemas Comunes**

#### **"Error al cargar archivo"**
**Causas posibles:**
- Formato de archivo incorrecto
- Archivo muy grande (>200MB)
- Columnas obligatorias faltantes

**Soluciones:**
- Verifica formato CSV
- Divide archivos grandes
- Revisa estructura de columnas

#### **"Geocercas no clasificadas"**
**Causas posibles:**
- Nombres de geocercas no estándar
- Geocercas nuevas no reconocidas

**Soluciones:**
- Revisa nombres en archivo original
- Contacta soporte para agregar nuevas geocercas

#### **"Sin datos para análisis"**
**Causas posibles:**
- Filtros muy restrictivos
- Datos insuficientes en el período

**Soluciones:**
- Amplía rango de fechas
- Revisa filtros aplicados
- Verifica calidad de datos GPS

### **🔧 Optimización de Performance**

#### **Para archivos grandes:**
- Filtra por fechas antes de subir
- Usa rangos de tiempo específicos
- Considera análisis por vehículo individual

#### **Para análisis frecuente:**
- Mantén ventana del navegador abierta
- Usa filtros para análisis específicos
- Descarga resultados importantes

---

## 📞 **Soporte y Contacto**

### **🆘 Soporte Inmediato**
- **Chat interno**: Equipo de TI
- **Email**: soporte@tmetal.com
- **Teléfono**: Ext. 1234 (horario de oficina)

### **📚 Recursos Adicionales**
- **Manual técnico**: Para administradores
- **Videos tutoriales**: En portal interno
- **FAQ**: Preguntas frecuentes actualizadas

### **🔄 Actualizaciones**
- **Notificaciones**: Por email cuando hay nuevas versiones
- **Changelog**: Lista de mejoras y correcciones
- **Capacitación**: Sesiones cuando hay cambios importantes

---

## 📈 **Mejores Prácticas**

### **✅ Recomendaciones Generales**

1. **Consistencia en datos**: Mantén nomenclatura estándar
2. **Análisis regular**: Revisa datos diariamente
3. **Acción rápida**: Responde a anomalías inmediatamente
4. **Documentación**: Registra acciones tomadas
5. **Colaboración**: Comparte insights con el equipo

### **🎯 Tips para Máximo Valor**

- **Combina** análisis cuantitativo con conocimiento operacional
- **Correlaciona** datos con eventos externos (clima, mantenimiento)
- **Usa** filtros para análisis específicos y detallados
- **Exporta** datos importantes para análisis posterior
- **Comparte** hallazgos con stakeholders relevantes

---

*Esta guía es un documento vivo que se actualiza regularmente. Para sugerencias o mejoras, contacta al equipo de desarrollo.*

**Última actualización**: Enero 2025  
**Versión de la aplicación**: 6.0 Mejorado  
**Próxima revisión**: Febrero 2025