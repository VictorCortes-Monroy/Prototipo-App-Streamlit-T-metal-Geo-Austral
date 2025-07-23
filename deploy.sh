#!/bin/bash

# 🚀 Script de Deployment - T-Metal BI Operacional
# Versión: 2.0.0

echo "🚀 Iniciando deployment de T-Metal BI Operacional v2.0.0"
echo "=================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "app5.py" ]; then
    echo "❌ Error: No se encontró app5.py en el directorio actual"
    exit 1
fi

# Verificar estado de Git
echo "📋 Verificando estado del repositorio..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Hay cambios sin committear. ¿Deseas continuar? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelado"
        exit 1
    fi
fi

# Verificar que las pruebas pasen
echo "🧪 Ejecutando pruebas automatizadas..."
if python test_app5.py; then
    echo "✅ Pruebas pasaron exitosamente"
else
    echo "❌ Las pruebas fallaron. ¿Deseas continuar? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelado"
        exit 1
    fi
fi

# Commit y push si hay cambios
echo "📤 Subiendo cambios a GitHub..."
git add .
git commit -m "deploy: Preparación para deployment v2.0.0"
git push origin main

echo "✅ Deployment preparado exitosamente!"
echo ""
echo "🌐 Para hacer deployment en Streamlit Cloud:"
echo "1. Ve a https://share.streamlit.io"
echo "2. Inicia sesión con GitHub"
echo "3. Click en 'New app'"
echo "4. Repositorio: VictorCortes-Monroy/Prototipo-App-Streamlit-T-metal-Geo-Austral"
echo "5. Branch: main"
echo "6. File path: app5.py"
echo "7. Click 'Deploy!'"
echo ""
echo "🔗 URL de tu aplicación será: https://[app-name]-[username].streamlit.app"
echo ""
echo "📊 Para monitorear el deployment:"
echo "- Revisa los logs en Streamlit Cloud"
echo "- Prueba todas las funcionalidades"
echo "- Verifica que los datos de prueba funcionen"
echo ""
echo "🎉 ¡Listo para producción!" 