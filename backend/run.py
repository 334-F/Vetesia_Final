"""
run.py
Punto de entrada del backend en desarrollo.
Para producción se usa gunicorn (ver Dockerfile).
"""
import os
from app import create_app

config_name = os.getenv("FLASK_ENV", "dev")
app = create_app(config_name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=(config_name == "dev"))
