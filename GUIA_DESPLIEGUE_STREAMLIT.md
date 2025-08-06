# 🚀 **GUÍA DE DESPLIEGUE - Streamlit Cloud**
## *T-Metal BI Operacional v6 Mejorado*

---

## 🎯 **Preparación para Despliegue**

### **📋 Pre-requisitos**

#### **🔧 Archivos Necesarios**
- [ ] `app6_mejorado.py` - Aplicación principal
- [ ] `requirements.txt` - Dependencias de Python
- [ ] `README.md` - Documentación del repositorio
- [ ] `.streamlit/config.toml` - Configuración de Streamlit (opcional)

#### **🌐 Cuentas Requeridas**
- [ ] **GitHub Account** - Para repositorio del código
- [ ] **Streamlit Cloud Account** - Para hosting gratuito
- [ ] **Email corporativo** - Para notificaciones y soporte

---

## 📦 **Preparación del Repositorio**

### **1️⃣ Crear Repositorio GitHub**

```bash
# Crear nuevo repositorio
git init
git add .
git commit -m "Initial commit: T-Metal BI Operacional v6"
git branch -M main
git remote add origin https://github.com/tu-organizacion/tmetal-bi-operacional.git
git push -u origin main
```

### **2️⃣ Estructura de Archivos Recomendada**

```
tmetal-bi-operacional/
├── app6_mejorado.py                 # Aplicación principal
├── requirements.txt                 # Dependencias
├── README.md                       # Documentación
├── DOCUMENTACION_APP6_MEJORADO.md  # Documentación técnica
├── GUIA_USUARIO_PRODUCCION.md      # Guía de usuario
├── .streamlit/
│   └── config.toml                 # Configuración
├── assets/
│   ├── logo.png                    # Logo corporativo
│   └── favicon.ico                 # Favicon
└── docs/
    ├── screenshots/                # Capturas de pantalla
    └── examples/                   # Archivos de ejemplo
```

### **3️⃣ Archivo requirements.txt**

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
altair>=5.0.0
folium>=0.14.0
streamlit-folium>=0.13.0
scikit-learn>=1.3.0
xlsxwriter>=3.1.0
unicodedata2>=15.0.0
```

### **4️⃣ Configuración Streamlit (.streamlit/config.toml)**

```toml
[global]
developmentMode = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B35"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
caching = true
displayEnabled = true
```

### **5️⃣ README.md para el Repositorio**

```markdown
# 🏭 T-Metal BI Operacional

Aplicación web para análisis de datos GPS de flota minera.

## 🚀 Despliegue

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tu-app.streamlit.app)

## 📊 Características

- Análisis de transiciones entre geocercas
- Detección de detenciones anómalas
- Visualizaciones interactivas
- Exportación de datos

## 🔧 Instalación Local

```bash
pip install -r requirements.txt
streamlit run app6_mejorado.py
```

## 📋 Documentación

- [Guía de Usuario](GUIA_USUARIO_PRODUCCION.md)
- [Documentación Técnica](DOCUMENTACION_APP6_MEJORADO.md)
```

---

## 🌐 **Despliegue en Streamlit Cloud**

### **1️⃣ Acceso a Streamlit Cloud**

1. **Visita**: https://share.streamlit.io
2. **Inicia sesión** con tu cuenta GitHub
3. **Autoriza** el acceso a tus repositorios

### **2️⃣ Crear Nueva App**

1. **Haz clic** en "New app"
2. **Selecciona** tu repositorio
3. **Configura** los parámetros:
   - **Repository**: `tu-organizacion/tmetal-bi-operacional`
   - **Branch**: `main`
   - **Main file path**: `app6_mejorado.py`
   - **App URL**: `tmetal-bi-operacional` (personalizable)

### **3️⃣ Configuración Avanzada**

#### **🔒 Variables de Entorno (si es necesario)**
```bash
# En Streamlit Cloud > App Settings > Secrets
[secrets]
API_KEY = "tu-api-key-si-es-necesario"
DATABASE_URL = "url-de-base-de-datos-si-aplica"
```

#### **🎨 Configuración de Dominio Personalizado**
- **Solo en planes pagos** de Streamlit Cloud
- **Configuración**: App Settings > General > Custom domain
- **DNS**: Apuntar CNAME a `share.streamlit.io`

---

## ⚙️ **Configuración de Producción**

### **🔧 Optimizaciones de Performance**

#### **En app6_mejorado.py - Agregar al inicio:**
```python
import streamlit as st

# Configuración de página optimizada para producción
st.set_page_config(
    page_title="T-Metal BI Operacional",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:soporte@tmetal.com',
        'Report a bug': 'mailto:dev@tmetal.com',
        'About': "T-Metal BI Operacional v6 - Análisis de Flota Minera"
    }
)

# Cache para mejorar performance
@st.cache_data
def load_and_process_data(uploaded_file):
    # Tu lógica de carga de datos aquí
    pass
```

### **📊 Monitoreo y Analytics**

#### **Google Analytics (opcional)**
```python
# Agregar al final de app6_mejorado.py
st.markdown("""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_TRACKING_ID');
</script>
""", unsafe_allow_html=True)
```

### **🔒 Seguridad y Acceso**

#### **Autenticación Básica (opcional)**
```python
# Agregar al inicio de la aplicación
def check_password():
    def password_entered():
        if st.session_state["password"] == "tu-password-seguro":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

---

## 📈 **Mantenimiento y Actualizaciones**

### **🔄 Proceso de Actualización**

#### **1. Desarrollo Local**
```bash
# Hacer cambios en app6_mejorado.py
# Probar localmente
streamlit run app6_mejorado.py

# Commit y push
git add .
git commit -m "feat: nueva funcionalidad X"
git push origin main
```

#### **2. Despliegue Automático**
- **Streamlit Cloud** detecta cambios automáticamente
- **Redepliegue** ocurre en 1-2 minutos
- **Notificación** por email del resultado

### **📊 Monitoreo de la Aplicación**

#### **Métricas Importantes**
- **Tiempo de respuesta**: < 3 segundos para carga inicial
- **Uso de memoria**: < 500MB por sesión
- **Errores**: Monitorear logs de Streamlit Cloud
- **Usuarios concurrentes**: Límite según plan

#### **Logs y Debugging**
```python
# Agregar logging para producción
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usar en puntos críticos
logger.info("Datos cargados exitosamente")
logger.error(f"Error procesando datos: {error}")
```

---

## 🚨 **Troubleshooting de Despliegue**

### **❌ Problemas Comunes**

#### **"ModuleNotFoundError"**
**Causa**: Dependencias faltantes en requirements.txt
**Solución**:
```bash
# Generar requirements.txt actualizado
pip freeze > requirements.txt
git add requirements.txt
git commit -m "fix: actualizar dependencias"
git push
```

#### **"Memory Limit Exceeded"**
**Causa**: Archivos muy grandes o memory leaks
**Solución**:
```python
# Agregar límites de memoria
@st.cache_data(max_entries=3)
def process_data(df):
    # Procesar datos con límite de cache
    return df

# Limpiar cache periódicamente
if st.button("Limpiar Cache"):
    st.cache_data.clear()
```

#### **"App is Sleeping"**
**Causa**: Inactividad por más de 7 días (plan gratuito)
**Solución**:
- **Visitar la app** regularmente
- **Upgrade a plan pagado** para apps críticas
- **Configurar health checks** automáticos

### **🔧 Optimizaciones Avanzadas**

#### **Lazy Loading de Componentes**
```python
# Cargar componentes pesados solo cuando se necesiten
@st.cache_resource
def load_heavy_component():
    # Componente pesado (mapas, gráficos complejos)
    return component

# Usar solo cuando se necesite
if st.checkbox("Mostrar mapa"):
    component = load_heavy_component()
    st.plotly_chart(component)
```

#### **Compresión de Datos**
```python
import gzip
import pickle

@st.cache_data
def compress_data(df):
    # Comprimir datos grandes
    compressed = gzip.compress(pickle.dumps(df))
    return compressed

def decompress_data(compressed):
    return pickle.loads(gzip.decompress(compressed))
```

---

## 📞 **Soporte Post-Despliegue**

### **🆘 Canales de Soporte**

#### **Streamlit Cloud**
- **Status Page**: https://status.streamlit.io
- **Community Forum**: https://discuss.streamlit.io
- **Documentation**: https://docs.streamlit.io

#### **Soporte Interno**
- **Email**: dev@tmetal.com
- **Slack**: #streamlit-support
- **Documentación**: Wiki interno

### **📋 Checklist Post-Despliegue**

- [ ] **URL funcionando** correctamente
- [ ] **Todas las funcionalidades** operativas
- [ ] **Performance** aceptable (< 3s carga inicial)
- [ ] **Logs** configurados y funcionando
- [ ] **Backup** del código en GitHub
- [ ] **Documentación** actualizada
- [ ] **Equipo capacitado** en el uso
- [ ] **Monitoreo** configurado
- [ ] **Plan de mantenimiento** establecido

---

## 🔮 **Próximos Pasos**

### **🚀 Mejoras Futuras**

1. **Autenticación SSO**: Integración con Active Directory
2. **Base de Datos**: Almacenamiento persistente
3. **API REST**: Endpoints para integraciones
4. **Mobile App**: Versión para dispositivos móviles
5. **Machine Learning**: Predicción de anomalías

### **📈 Escalamiento**

#### **Cuando considerar upgrade:**
- **> 100 usuarios concurrentes**
- **Archivos > 200MB regulares**
- **Necesidad de uptime 99.9%**
- **Requerimientos de seguridad avanzada**

#### **Alternativas de hosting:**
- **Streamlit Cloud Pro**: $20/mes por app
- **AWS ECS/Fargate**: Más control y escalabilidad
- **Google Cloud Run**: Serverless con auto-scaling
- **Azure Container Instances**: Integración con ecosistema Microsoft

---

*Esta guía se actualiza con cada nueva versión de Streamlit Cloud y mejores prácticas de la industria.*

**Última actualización**: Enero 2025  
**Streamlit Cloud Version**: 1.28+  
**Próxima revisión**: Febrero 2025