# 🚀 Guía de Deployment - T-Metal BI Operacional

## 🌐 **Opción 1: Streamlit Cloud (Recomendado)**

### **Ventajas:**
- ✅ **Gratuito** para aplicaciones públicas
- ✅ **Deployment automático** desde GitHub
- ✅ **Escalable** automáticamente
- ✅ **SSL incluido** (HTTPS)
- ✅ **Muy fácil** de configurar

### **Pasos:**

#### **1. Preparar el Repositorio**
```bash
# Verificar que todo esté committeado
git status
git push origin main
```

#### **2. Crear Cuenta en Streamlit Cloud**
1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Iniciar sesión con GitHub
3. Autorizar acceso al repositorio

#### **3. Deploy la Aplicación**
1. Click en "New app"
2. Seleccionar repositorio: `VictorCortes-Monroy/Prototipo-App-Streamlit-T-metal-Geo-Austral`
3. Branch: `main`
4. File path: `app5.py`
5. Click "Deploy!"

#### **4. Configuración Adicional**
```python
# En app5.py, agregar configuración de página
st.set_page_config(
    page_title="⛏️ T-Metal – BI Operacional",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## ☁️ **Opción 2: Heroku**

### **Ventajas:**
- ✅ **Escalable** y confiable
- ✅ **Integración** con GitHub
- ✅ **SSL incluido**
- ⚠️ **Pago** después del período gratuito

### **Archivos Necesarios:**

#### **1. Crear `setup.sh`**
```bash
mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"tu-email@ejemplo.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
```

#### **2. Crear `Procfile`**
```
web: sh setup.sh && streamlit run app5.py
```

#### **3. Crear `runtime.txt`**
```
python-3.10.0
```

### **Deployment:**
```bash
# Instalar Heroku CLI
# Crear app en Heroku
heroku create t-metal-bi-app

# Deploy
git push heroku main

# Abrir app
heroku open
```

---

## 🐳 **Opción 3: Docker + VPS**

### **Ventajas:**
- ✅ **Control total** del servidor
- ✅ **Escalable** según necesidades
- ✅ **Personalizable**
- ⚠️ **Requiere** conocimientos técnicos

### **Archivos Necesarios:**

#### **1. Crear `Dockerfile`**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app5.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### **2. Crear `docker-compose.yml`**
```yaml
version: '3.8'
services:
  t-metal-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped
```

### **Deployment:**
```bash
# Construir imagen
docker build -t t-metal-bi .

# Ejecutar contenedor
docker run -p 8501:8501 t-metal-bi

# O con docker-compose
docker-compose up -d
```

---

## ☁️ **Opción 4: Google Cloud Platform (GCP)**

### **Ventajas:**
- ✅ **Muy escalable**
- ✅ **Integración** con otros servicios Google
- ✅ **Confiable**
- ⚠️ **Costo** según uso

### **Pasos:**

#### **1. Crear `app.yaml`**
```yaml
runtime: python310
entrypoint: streamlit run app5.py --server.port=$PORT --server.address=0.0.0.0

env_variables:
  STREAMLIT_SERVER_PORT: 8080
  STREAMLIT_SERVER_ADDRESS: 0.0.0.0

automatic_scaling:
  target_cpu_utilization: 0.6
  min_instances: 1
  max_instances: 10
```

#### **2. Deploy**
```bash
# Instalar Google Cloud SDK
gcloud init
gcloud app deploy
```

---

## 🚀 **Opción 5: AWS (Amazon Web Services)**

### **Ventajas:**
- ✅ **Muy escalable**
- ✅ **Servicios integrados**
- ✅ **Confiable**
- ⚠️ **Complejo** de configurar

### **Servicios Recomendados:**
- **AWS Elastic Beanstalk**
- **AWS ECS (Docker)**
- **AWS Lambda + API Gateway**

---

## 📋 **Checklist de Deployment**

### **Pre-Deployment:**
- [ ] **Pruebas completas** ejecutadas
- [ ] **Documentación** actualizada
- [ ] **Variables de entorno** configuradas
- [ ] **Dependencias** verificadas
- [ ] **Archivos sensibles** removidos

### **Post-Deployment:**
- [ ] **URL de acceso** verificada
- [ ] **Funcionalidades** probadas
- [ ] **Rendimiento** monitoreado
- [ ] **SSL/HTTPS** configurado
- [ ] **Backup** configurado

---

## 🔧 **Configuración de Producción**

### **Variables de Entorno Recomendadas:**
```bash
# Configuración de Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false

# Configuración de la aplicación
T_METAL_ENVIRONMENT=production
T_METAL_LOG_LEVEL=INFO
```

### **Optimizaciones de Rendimiento:**
```python
# En app5.py
import streamlit as st

# Configuración de caché para mejorar rendimiento
@st.cache_data
def load_data(uploaded_file):
    return pd.read_csv(uploaded_file)

# Configuración de la página
st.set_page_config(
    page_title="⛏️ T-Metal – BI Operacional",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## 📊 **Monitoreo y Mantenimiento**

### **Métricas a Monitorear:**
- **Tiempo de respuesta** de la aplicación
- **Uso de memoria** y CPU
- **Número de usuarios** concurrentes
- **Errores** y excepciones
- **Tiempo de carga** de datos

### **Herramientas de Monitoreo:**
- **Streamlit Cloud**: Métricas básicas incluidas
- **Google Analytics**: Para análisis de usuarios
- **Sentry**: Para monitoreo de errores
- **Prometheus + Grafana**: Para métricas avanzadas

---

## 🚨 **Consideraciones de Seguridad**

### **Recomendaciones:**
- ✅ **HTTPS obligatorio** en producción
- ✅ **Validación** de archivos subidos
- ✅ **Límites** de tamaño de archivo
- ✅ **Rate limiting** para prevenir abuso
- ✅ **Logs** de auditoría

### **Configuración de Seguridad:**
```python
# Validación de archivos
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file(uploaded_file):
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("Archivo demasiado grande")
        return False
    if not uploaded_file.name.endswith('.csv'):
        st.error("Solo se permiten archivos CSV")
        return False
    return True
```

---

## 💰 **Costos Estimados**

### **Streamlit Cloud:**
- **Gratuito** para aplicaciones públicas
- **$10/mes** para aplicaciones privadas

### **Heroku:**
- **$7/mes** para dyno básico
- **$25/mes** para dyno estándar

### **GCP/AWS:**
- **$5-50/mes** dependiendo del tráfico
- **Escalable** según uso

---

## 🎯 **Recomendación Final**

### **Para Inicio Rápido:**
1. **Streamlit Cloud** - Gratuito y fácil
2. **Heroku** - Si necesitas privacidad

### **Para Producción Empresarial:**
1. **Docker + VPS** - Control total
2. **GCP/AWS** - Escalabilidad empresarial

### **Próximos Pasos:**
1. Elegir plataforma de deployment
2. Configurar variables de entorno
3. Hacer deployment inicial
4. Configurar monitoreo
5. Documentar procedimientos de mantenimiento 