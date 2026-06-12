"""
app.py
Punto de entrada alternativo para iniciar el backend desde la carpeta 'backend'.
"""
import os
import sys

# Evitamos conflicto de nombres quitando el directorio actual del path de importacion
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(current_dir)]

# Aniadimos el directorio actual al final para otros modulos
sys.path.append(current_dir)

# Importamos la app buscando en el directorio padre
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.app import create_app

config_name = os.getenv("FLASK_ENV", "dev")
app = create_app(config_name)

if __name__ == "__main__":
    print("Iniciando servidor backend de VetEsia en http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=(config_name == "dev"))
