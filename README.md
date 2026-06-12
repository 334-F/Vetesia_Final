# VetÉsia

E-commerce de productos veterinarios y uniformidad personalizable.
Proyecto final del Ciclo Superior DAW · IES Pío Baroja · Curso 2025-2026.

## Equipo

| Integrante | Responsabilidad |
|---|---|
| Felipe Xu | Backend, base de datos, lógica de negocio, facturas PDF |
| Samuel Marugán | Frontend, UI/UX, integración con la API |
| Jean Paul Milachay | DevOps, Docker, despliegue, seguridad |

## Tecnologías

- **Frontend**: HTML5, CSS3, Bootstrap 5.3, JavaScript vanilla
- **Backend**: Python 3.11 + Flask + SQLAlchemy + JWT
- **Base de datos**: MySQL 8
- **Pasarela de pago**: Stripe (modo test)
- **PDF**: ReportLab
- **Email**: Flask-Mail (SMTP)
- **Contenedores**: Docker + Docker Compose
- **Servidor web**: Nginx

## Estructura del proyecto

```
vetesia/
├── frontend/               # HTML + CSS + JS 
│   ├── index.html          # Home
│   ├── pages/              # Catálogo, ficha, carrito, checkout, cuenta, admin
│   ├── css/style.css
│   ├── js/                 # api.js, auth.js, cart.js, ui.js, layout.js
│   └── img/
├── backend/                # API Flask (Felipe)
│   ├── app/
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── routes/         # Endpoints REST
│   │   ├── services/       # Lógica de negocio (precios, facturas, emails, Stripe)
│   │   └── utils/          # Decoradores y helpers
│   ├── tests/              # Tests con pytest
│   ├── scripts/            # Scripts auxiliares
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── sql/
│   └── vetesia_schema.sql  # Esquema completo + datos de prueba
├── docs/                   # Documentación del proyecto (Word)
├── docker-compose.yml
├── nginx.conf
├── install.sh              # Script de instalación rápida
└── README.md
```

## Puesta en marcha

### Opción A: Docker (recomendada, todo en un comando)

```bash
git clone <tu-repositorio>
cd vetesia
cp backend/.env.example backend/.env
docker compose up --build
```

Cuando termine de construir, abre <http://localhost> en el navegador.

### Opción B: Instalación local (sin Docker)

Requiere: Python 3.11+, MySQL 8 corriendo en localhost.

```bash
# 1. Cargar la BBDD
mysql -u root -p < sql/vetesia_schema.sql

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edita el DATABASE_URL si hace falta
python scripts/reset_passwords.py    # genera hashes bcrypt válidos
python run.py

# 3. En otra terminal: frontend
cd frontend
python3 -m http.server 8080

# 4. Abre http://localhost:8080
```

O simplemente ejecuta el script automático:

```bash
chmod +x install.sh && ./install.sh
```

## Usuarios de prueba

Tras cargar el esquema y ejecutar `reset_passwords.py`:

| Email | Contraseña | Rol |
|---|---|---|
| admin@vetesia.com | admin123 | administrador |
| maria@example.com | cliente123 | cliente particular |
| carlos@clinica.com | cliente123 | cliente profesional |

## Tarjeta de prueba para Stripe

En el checkout, elige "Tarjeta" como método de pago. Usa esta tarjeta de test:
- **Número**: 4242 4242 4242 4242
- **Caducidad**: cualquier fecha futura (ej: 12/29)
- **CVC**: cualquier 3 dígitos (ej: 123)

## Despliegue en producción

### Render.com (gratis, ~15 minutos)

1. Crea cuenta en <https://render.com>
2. Conecta tu repositorio de GitHub
3. Crea un servicio MySQL desde el dashboard de Render
4. Crea un Web Service con la carpeta `backend/`. Configura las variables de entorno desde `.env.example`
5. Crea un Static Site con la carpeta `frontend/`
6. En `frontend/js/config.js` cambia `API_BASE_URL` a la URL de tu backend en Render

### Railway.app (alternativa)

Similar a Render, con plan gratuito limitado. Soporta despliegue desde GitHub.

### VPS propio (DigitalOcean, Hostinger)

Usa el `docker-compose.yml` que viene incluido. Configura un dominio y obten certificado SSL con Let's Encrypt.

## Endpoints principales de la API

### Autenticación
- `POST /api/auth/register` — Registro
- `POST /api/auth/login` — Login (devuelve JWT)
- `GET /api/auth/me` — Datos del usuario actual

### Catálogo
- `GET /api/productos` — Listado con filtros
- `GET /api/productos/:id` — Ficha
- `GET /api/categorias` — Categorías

### Pedidos
- `GET /api/pedidos` — Historial del usuario
- `POST /api/pedidos` — Crear pedido (checkout)
- `GET /api/pedidos/:id/factura` — Descargar PDF
- `PATCH /api/pedidos/:id/cancelar` — Cancelar

### Mi cuenta
- `GET /api/usuarios/me` / `PATCH /api/usuarios/me`
- `GET /api/direcciones` / `POST` / `PATCH` / `DELETE`
- `POST /api/resenas`

### Admin
- `GET /api/admin/pedidos`
- `PATCH /api/admin/pedidos/:id/estado`
- `GET /api/admin/resenas/pendientes`
- `PATCH /api/admin/resenas/:id/verificar`
- `GET/POST/PATCH/DELETE /api/admin/promociones`
- `GET /api/admin/informes/stock-bajo`
- `GET /api/admin/informes/ventas-por-mes`
- `GET /api/admin/informes/productos-mas-vendidos`

## Páginas del frontend

| Ruta | Página |
|---|---|
| `/` | Home con productos destacados |
| `/pages/catalogo.html` | Catálogo con filtros |
| `/pages/producto.html?id=X` | Ficha de producto |
| `/pages/carrito.html` | Carrito |
| `/pages/checkout.html` | Finalizar compra |
| `/pages/pedido-confirmado.html?id=X` | Confirmación |
| `/pages/login.html` / `/pages/registro.html` | Auth |
| `/pages/mi-cuenta.html` | Datos personales |
| `/pages/mis-pedidos.html` | Historial |
| `/pages/mis-direcciones.html` | Direcciones |
| `/pages/admin.html` | Panel del administrador |

## Pruebas

```bash
cd backend
source venv/bin/activate
pytest
```

## Documentación adicional

- `docs/01_VetEsia_Documento_Maestro.docx` — Documento principal del proyecto
- `docs/02_VetEsia_Defensa_Felipe.docx` — Defensa individual

## Licencia

Proyecto académico. Todos los derechos reservados a los autores.
