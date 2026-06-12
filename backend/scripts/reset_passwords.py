"""
Script auxiliar para regenerar las contraseñas de los usuarios de prueba
con hashes de bcrypt válidos. Se ejecuta una sola vez tras cargar el seed.

Uso:
    cd backend
    python scripts/reset_passwords.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Usuario

USUARIOS_PRUEBA = {
    "admin@vetesia.com": "admin123",
    "maria@example.com": "cliente123",
    "carlos@clinica.com": "cliente123",
}

app = create_app("dev")
with app.app_context():
    for email, password in USUARIOS_PRUEBA.items():
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            usuario.set_password(password)
            print(f"✓ Contraseña actualizada para {email}")
        else:
            print(f"✗ Usuario no encontrado: {email}")
    db.session.commit()
    print("\nListo. Ya puedes iniciar sesión con las credenciales del README.")
