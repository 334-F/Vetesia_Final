#!/bin/bash
# install.sh · Script de instalación rápida de VetÉsia en desarrollo
# Asume: Python 3.11+, MySQL 8 corriendo en localhost, root sin contraseña (o ajustar)

set -e

echo "=== VetÉsia · Instalación rápida ==="
echo ""

# 1. Cargar el esquema en MySQL
echo "1. Cargando esquema de BBDD en MySQL..."
if command -v mysql &> /dev/null; then
    mysql -u root < sql/vetesia_schema.sql && echo "   ✓ BBDD creada"
else
    echo "   ⚠ MySQL no encontrado. Carga sql/vetesia_schema.sql manualmente."
fi

# 2. Crear entorno virtual y dependencias
echo ""
echo "2. Instalando dependencias Python..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo "   ✓ Dependencias instaladas"

# 3. Crear .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   ✓ Archivo .env creado (revísalo y edita las claves)"
fi

# 4. Regenerar contraseñas de prueba
echo ""
echo "3. Generando hashes bcrypt para usuarios de prueba..."
python scripts/reset_passwords.py || echo "   ⚠ No se pudieron regenerar (¿la BBDD está creada?)"

cd ..

echo ""
echo "=== Instalación completa ==="
echo ""
echo "Para arrancar:"
echo "  Terminal 1 (backend):  cd backend && source venv/bin/activate && python run.py"
echo "  Terminal 2 (frontend): cd frontend && python3 -m http.server 8080"
echo ""
echo "Luego abre http://localhost:8080 en el navegador."
echo ""
echo "Usuarios de prueba:"
echo "  admin@vetesia.com / admin123  (administrador)"
echo "  maria@example.com / cliente123 (cliente)"
