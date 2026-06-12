-- =====================================================================
-- VetÉsia · Script SQL completo
-- Base de datos: MySQL 8
-- Autor: Felipe Xu (Grupo 4 · DAW 2BIL · IES Pío Baroja · 2025-2026)
-- =====================================================================
-- Este script crea la base de datos completa de VetÉsia, una tienda
-- online B2C de productos veterinarios y uniformidad personalizable.
-- Incluye 14 tablas en 3FN, sus relaciones, índices y datos de prueba.
-- =====================================================================

DROP DATABASE IF EXISTS vetesia;
CREATE DATABASE vetesia
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE vetesia;

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- TABLAS DE CATÁLOGOS (datos maestros)
-- =====================================================================

-- Tipos de cliente: particular o profesional (permite escalar a B2B)
CREATE TABLE TiposCliente (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    descripcion     TEXT,
    descuento       DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Porcentaje de descuento aplicable',
    activo          BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Métodos de pago disponibles
CREATE TABLE MetodosPago (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nombre              VARCHAR(50) NOT NULL UNIQUE,
    descripcion         TEXT,
    requiere_pasarela   BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'TRUE para tarjeta, FALSE para transferencia/contrareembolso',
    activo              BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Zonas de envío con su coste y plazo
CREATE TABLE ZonasEnvio (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    coste_envio     DECIMAL(10,2) NOT NULL,
    plazo_dias      INT NOT NULL,
    activa          BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Tipos de servicio para personalización (uniformidad)
CREATE TABLE TiposServicio (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    nombre                  VARCHAR(50) NOT NULL UNIQUE,
    descripcion             TEXT,
    precio_extra            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    dtg                     BOOLEAN NOT NULL DEFAULT FALSE,
    bordado                 BOOLEAN NOT NULL DEFAULT FALSE,
    revision_manual         BOOLEAN NOT NULL DEFAULT FALSE,
    etiquetado              BOOLEAN NOT NULL DEFAULT FALSE,
    produccion_prioritaria  BOOLEAN NOT NULL DEFAULT FALSE,
    activo                  BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Categorías de productos (con jerarquía simple padre-hijo)
CREATE TABLE Categorias (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    descripcion         TEXT,
    categoria_padre_id  INT NULL,
    imagen_url          VARCHAR(255),
    activa              BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_cat_padre FOREIGN KEY (categoria_padre_id)
        REFERENCES Categorias(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_cat_padre ON Categorias(categoria_padre_id);

-- =====================================================================
-- USUARIOS
-- =====================================================================

CREATE TABLE Usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tipo_cliente_id INT NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    apellidos       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NULL COMMENT 'Hash bcrypt coste 12. NULL para invitados (compran sin cuenta)',
    telefono        VARCHAR(15),
    direccion       VARCHAR(200) COMMENT 'Dirección de contacto/facturación, no de envío',
    rol             ENUM('cliente', 'admin', 'invitado') NOT NULL DEFAULT 'cliente',
    fecha_registro  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_usr_tipo FOREIGN KEY (tipo_cliente_id)
        REFERENCES TiposCliente(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_usr_email ON Usuarios(email);
CREATE INDEX idx_usr_rol ON Usuarios(rol);

-- Direcciones de envío (un usuario puede tener varias)
CREATE TABLE DireccionesEnvio (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id          INT NOT NULL,
    alias               VARCHAR(50) NOT NULL COMMENT 'Casa, Trabajo, etc.',
    destinatario        VARCHAR(150) NOT NULL,
    calle               VARCHAR(200) NOT NULL,
    numero              VARCHAR(10),
    piso                VARCHAR(20),
    codigo_postal       VARCHAR(10) NOT NULL,
    municipio           VARCHAR(100) NOT NULL,
    provincia           VARCHAR(100) NOT NULL,
    telefono_contacto   VARCHAR(15),
    predeterminada      BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_dir_usr FOREIGN KEY (usuario_id)
        REFERENCES Usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_dir_usuario ON DireccionesEnvio(usuario_id);

-- =====================================================================
-- CATÁLOGO DE PRODUCTOS
-- =====================================================================

CREATE TABLE Productos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id    INT NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    tipo            ENUM('estandar', 'personalizable') NOT NULL DEFAULT 'estandar',
    precio_base     DECIMAL(10,2) NOT NULL,
    stock           INT NOT NULL DEFAULT 0,
    stock_minimo    INT NOT NULL DEFAULT 5 COMMENT 'Por debajo de esto, alerta al admin',
    imagen_url      VARCHAR(255),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_alta      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prod_cat FOREIGN KEY (categoria_id)
        REFERENCES Categorias(id) ON DELETE RESTRICT,
    CONSTRAINT chk_prod_precio CHECK (precio_base >= 0),
    CONSTRAINT chk_prod_stock CHECK (stock >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_prod_cat ON Productos(categoria_id);
CREATE INDEX idx_prod_activo ON Productos(activo);

-- Precios escalados por cantidad (opcional por producto)
CREATE TABLE PreciosEscalados (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    producto_id         INT NOT NULL,
    cantidad_min        INT NOT NULL,
    cantidad_max        INT NULL COMMENT 'NULL = sin límite superior',
    precio_unitario     DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_pe_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE CASCADE,
    CONSTRAINT chk_pe_cantidad CHECK (cantidad_min > 0),
    CONSTRAINT chk_pe_precio CHECK (precio_unitario >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_pe_prod ON PreciosEscalados(producto_id);

-- Promociones y descuentos temporales
CREATE TABLE Promociones (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     TEXT,
    tipo            ENUM('porcentaje', 'fijo') NOT NULL,
    valor           DECIMAL(10,2) NOT NULL COMMENT 'Porcentaje (0-100) o cantidad fija',
    fecha_inicio    DATETIME NOT NULL,
    fecha_fin       DATETIME NOT NULL,
    producto_id     INT NULL COMMENT 'NULL = aplica a categoría o global',
    categoria_id    INT NULL COMMENT 'NULL = aplica a producto concreto o global',
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_promo_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE CASCADE,
    CONSTRAINT fk_promo_cat FOREIGN KEY (categoria_id)
        REFERENCES Categorias(id) ON DELETE CASCADE,
    CONSTRAINT chk_promo_fechas CHECK (fecha_fin > fecha_inicio),
    CONSTRAINT chk_promo_valor CHECK (valor >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_promo_activa ON Promociones(activa, fecha_inicio, fecha_fin);

-- =====================================================================
-- PEDIDOS DEL CLIENTE
-- =====================================================================

CREATE TABLE Pedidos (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id          INT NOT NULL,
    direccion_envio_id  INT NOT NULL,
    metodo_pago_id      INT NOT NULL,
    zona_envio_id       INT NOT NULL,
    fecha               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado              ENUM('pendiente_pago','pagado','preparando','enviado','entregado','cancelado','reembolsado')
                            NOT NULL DEFAULT 'pendiente_pago',
    subtotal            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    coste_envio         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    descuento           DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total               DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    notas               TEXT,
    transaccion_id      VARCHAR(255) NULL COMMENT 'ID devuelto por la pasarela de pago',
    factura_url         VARCHAR(255) NULL COMMENT 'Ruta al PDF generado',
    CONSTRAINT fk_ped_usr FOREIGN KEY (usuario_id)
        REFERENCES Usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ped_dir FOREIGN KEY (direccion_envio_id)
        REFERENCES DireccionesEnvio(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ped_pago FOREIGN KEY (metodo_pago_id)
        REFERENCES MetodosPago(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ped_zona FOREIGN KEY (zona_envio_id)
        REFERENCES ZonasEnvio(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_ped_usr ON Pedidos(usuario_id);
CREATE INDEX idx_ped_estado ON Pedidos(estado);
CREATE INDEX idx_ped_fecha ON Pedidos(fecha);

-- Líneas del pedido (detalle)
CREATE TABLE LineasPedido (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id           INT NOT NULL,
    producto_id         INT NOT NULL,
    tipo_servicio_id    INT NULL COMMENT 'Solo para productos personalizables',
    cantidad            INT NOT NULL,
    precio_unitario     DECIMAL(10,2) NOT NULL COMMENT 'Precio aplicado en el momento de la compra',
    personalizacion     TEXT COMMENT 'Texto/instrucciones de personalización',
    archivo_diseno_url  VARCHAR(255) COMMENT 'Ruta al archivo subido por el cliente',
    subtotal            DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_lp_ped FOREIGN KEY (pedido_id)
        REFERENCES Pedidos(id) ON DELETE CASCADE,
    CONSTRAINT fk_lp_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_lp_serv FOREIGN KEY (tipo_servicio_id)
        REFERENCES TiposServicio(id) ON DELETE SET NULL,
    CONSTRAINT chk_lp_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB;

CREATE INDEX idx_lp_ped ON LineasPedido(pedido_id);
CREATE INDEX idx_lp_prod ON LineasPedido(producto_id);

-- =====================================================================
-- PROVEEDORES (lado administrador)
-- =====================================================================

CREATE TABLE Proveedores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    persona_contacto VARCHAR(100),
    email           VARCHAR(150),
    telefono        VARCHAR(15),
    direccion       VARCHAR(200),
    condiciones     TEXT,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Relación N a N entre productos y proveedores
CREATE TABLE ProductosProveedor (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id        INT NOT NULL,
    producto_id         INT NOT NULL,
    precio_compra       DECIMAL(10,2) NOT NULL,
    plazo_entrega_dias  INT,
    es_principal        BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_pp_prov FOREIGN KEY (proveedor_id)
        REFERENCES Proveedores(id) ON DELETE CASCADE,
    CONSTRAINT fk_pp_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE CASCADE,
    CONSTRAINT uq_pp UNIQUE (proveedor_id, producto_id)
) ENGINE=InnoDB;

-- Pedidos de reposición al proveedor
CREATE TABLE PedidosProveedor (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id    INT NOT NULL,
    admin_id        INT NOT NULL COMMENT 'Usuario admin que creó el pedido',
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado          ENUM('creado','enviado','recibido','cancelado') NOT NULL DEFAULT 'creado',
    total           DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    notas           TEXT,
    CONSTRAINT fk_pproV_prov FOREIGN KEY (proveedor_id)
        REFERENCES Proveedores(id) ON DELETE RESTRICT,
    CONSTRAINT fk_pproV_admin FOREIGN KEY (admin_id)
        REFERENCES Usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_pprov_estado ON PedidosProveedor(estado);

-- Líneas del pedido a proveedor
CREATE TABLE LineasPedidoProveedor (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    pedido_proveedor_id     INT NOT NULL,
    producto_id             INT NOT NULL,
    cantidad                INT NOT NULL,
    precio_unitario         DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_lpp_ped FOREIGN KEY (pedido_proveedor_id)
        REFERENCES PedidosProveedor(id) ON DELETE CASCADE,
    CONSTRAINT fk_lpp_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE RESTRICT,
    CONSTRAINT chk_lpp_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB;

-- =====================================================================
-- RESEÑAS
-- =====================================================================

CREATE TABLE Resenas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    producto_id     INT NOT NULL,
    valoracion      TINYINT NOT NULL COMMENT '1 a 5 estrellas',
    texto           TEXT,
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verificada      BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'El admin la verifica antes de publicar',
    CONSTRAINT fk_res_usr FOREIGN KEY (usuario_id)
        REFERENCES Usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_res_prod FOREIGN KEY (producto_id)
        REFERENCES Productos(id) ON DELETE CASCADE,
    CONSTRAINT chk_res_val CHECK (valoracion BETWEEN 1 AND 5),
    CONSTRAINT uq_res UNIQUE (usuario_id, producto_id)
) ENGINE=InnoDB;

CREATE INDEX idx_res_prod ON Resenas(producto_id, verificada);

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- DATOS DE PRUEBA (SEED)
-- =====================================================================

-- Tipos de cliente
INSERT INTO TiposCliente (nombre, descripcion, descuento) VALUES
    ('Particular', 'Dueño de mascota o usuario final', 0.00),
    ('Profesional', 'Clínica veterinaria o profesional del sector', 10.00);

-- Métodos de pago
INSERT INTO MetodosPago (nombre, descripcion, requiere_pasarela) VALUES
    ('Tarjeta', 'Pago con tarjeta de crédito o débito (Visa, Mastercard)', TRUE),
    ('Transferencia bancaria', 'Pago por transferencia con confirmación manual', FALSE),
    ('Contrarreembolso', 'Pago en efectivo en el momento de la entrega', FALSE),
    ('Bizum', 'Pago instantáneo por Bizum', TRUE);

-- Zonas de envío
INSERT INTO ZonasEnvio (nombre, coste_envio, plazo_dias) VALUES
    ('Península', 4.95, 3),
    ('Baleares', 9.95, 5),
    ('Canarias', 14.95, 7),
    ('Ceuta y Melilla', 14.95, 7);

-- Tipos de servicio de personalización
INSERT INTO TiposServicio (nombre, descripcion, precio_extra, dtg, bordado, revision_manual, etiquetado, produccion_prioritaria) VALUES
    ('Estándar', 'Personalización básica con DTG y revisión automática', 0.00, TRUE, FALSE, FALSE, FALSE, FALSE),
    ('Premium DTG', 'DTG de alta calidad con revisión manual y etiquetado', 4.95, TRUE, FALSE, TRUE, TRUE, FALSE),
    ('Premium Bordado', 'Bordado de alta definición con revisión y producción prioritaria', 9.95, FALSE, TRUE, TRUE, TRUE, TRUE);

-- Categorías
INSERT INTO Categorias (nombre, descripcion) VALUES
    ('Alimentacion', 'Comida seca y húmeda para perros y gatos'),
    ('Higiene y cuidado', 'Champús, cepillos, recortadores'),
    ('Salud y antiparasitarios', 'Pipetas, collares antipulgas, suplementos'),
    ('Accesorios', 'Correas, transportines, juguetes'),
    ('Uniformidad veterinaria', 'Batas, camisetas y sudaderas personalizables');

-- Usuarios (1 admin + 2 clientes)
-- Contraseñas hasheadas con bcrypt. Texto plano: 'admin123' y 'cliente123'
INSERT INTO Usuarios (tipo_cliente_id, nombre, apellidos, email, password_hash, telefono, direccion, rol) VALUES
    (1, 'Admin', 'Sistema', 'admin@vetesia.com', '$2b$12$LQv3c1yqBwEHFl4U5G5kKuKvJj1xQv4qZ6yU3vQ8L9xZ6yU3vQ8L9', '600000001', 'Oficinas VetÉsia, Madrid', 'admin'),
    (1, 'María', 'García López', 'maria@example.com', '$2b$12$LQv3c1yqBwEHFl4U5G5kKuKvJj1xQv4qZ6yU3vQ8L9xZ6yU3vQ8L9', '600000002', 'Calle Mayor 1, Madrid', 'cliente'),
    (2, 'Carlos', 'Ruiz Pérez', 'carlos@clinica.com', '$2b$12$LQv3c1yqBwEHFl4U5G5kKuKvJj1xQv4qZ6yU3vQ8L9xZ6yU3vQ8L9', '600000003', 'Av. Vetereinaria 22, Valencia', 'cliente');

-- Direcciones de envío
INSERT INTO DireccionesEnvio (usuario_id, alias, destinatario, calle, numero, piso, codigo_postal, municipio, provincia, telefono_contacto, predeterminada) VALUES
    (2, 'Casa', 'María García', 'Calle Mayor', '1', '3ºB', '28001', 'Madrid', 'Madrid', '600000002', TRUE),
    (2, 'Trabajo', 'María García', 'Gran Vía', '50', NULL, '28013', 'Madrid', 'Madrid', '600000002', FALSE),
    (3, 'Clínica', 'Clínica Vet Ruiz', 'Av. Veterinaria', '22', NULL, '46001', 'Valencia', 'Valencia', '600000003', TRUE);

-- Productos
INSERT INTO Productos (categoria_id, nombre, descripcion, tipo, precio_base, stock, stock_minimo, imagen_url) VALUES
    (1, 'Royal Canin Mini Adult 8kg', 'Alimentación seca para perros de raza pequeña adultos', 'estandar', 49.95, 50, 10, '/img/royal_canin_mini.jpg'),
    (1, 'Hill''s Science Diet Cat 3kg', 'Alimentación seca premium para gatos adultos', 'estandar', 29.95, 40, 10, '/img/hills_cat.jpg'),
    (2, 'Champú Pelo Largo 500ml', 'Champú especial para pelo largo y enredado', 'estandar', 12.50, 80, 15, '/img/champu_largo.jpg'),
    (3, 'Pipetas antipulgas pack 3 uds', 'Pipetas antiparasitarias de amplio espectro', 'estandar', 24.95, 100, 20, '/img/pipetas.jpg'),
    (4, 'Correa retráctil 5m', 'Correa retráctil para perros hasta 25kg', 'estandar', 18.95, 30, 5, '/img/correa.jpg'),
    (5, 'Bata veterinaria manga corta', 'Bata técnica personalizable para clínicas', 'personalizable', 24.95, 25, 5, '/img/bata_corta.jpg'),
    (5, 'Sudadera con capucha veterinaria', 'Sudadera técnica con bolsillo para personalizar', 'personalizable', 34.95, 20, 5, '/img/sudadera.jpg'),
    (5, 'Camiseta polo veterinaria', 'Polo técnico transpirable con opciones de bordado', 'personalizable', 19.95, 30, 5, '/img/polo.jpg');

-- Precios escalados (descuento por volumen en pipetas)
INSERT INTO PreciosEscalados (producto_id, cantidad_min, cantidad_max, precio_unitario) VALUES
    (4, 3, 5, 22.95),
    (4, 6, 9, 20.95),
    (4, 10, NULL, 18.95);

-- Promociones
INSERT INTO Promociones (nombre, descripcion, tipo, valor, fecha_inicio, fecha_fin, categoria_id, activa) VALUES
    ('Black Friday Alimentación', '20% en toda la alimentación', 'porcentaje', 20.00, '2026-11-27 00:00:00', '2026-11-30 23:59:59', 1, TRUE),
    ('Rebajas verano uniformidad', '15% en uniformidad veterinaria', 'porcentaje', 15.00, '2026-07-01 00:00:00', '2026-07-31 23:59:59', 5, TRUE);

-- Proveedores
INSERT INTO Proveedores (nombre, persona_contacto, email, telefono, direccion, condiciones, activo) VALUES
    ('Suministros Vet S.L.', 'Juan Pérez', 'jperez@suministrosvet.com', '910000001', 'Polígono Industrial, Madrid', 'Pago a 30 días, envío gratis pedidos > 500€', TRUE),
    ('TextilPro Uniformes', 'Ana Gómez', 'agomez@textilpro.com', '910000002', 'Polígono Industrial, Barcelona', 'Pago a 60 días, mínimo 100 unidades para personalización', TRUE);

-- Relación productos-proveedores
INSERT INTO ProductosProveedor (proveedor_id, producto_id, precio_compra, plazo_entrega_dias, es_principal) VALUES
    (1, 1, 32.00, 5, TRUE),
    (1, 2, 19.50, 5, TRUE),
    (1, 3, 7.50, 7, TRUE),
    (1, 4, 14.00, 5, TRUE),
    (1, 5, 11.00, 7, TRUE),
    (2, 6, 14.00, 10, TRUE),
    (2, 7, 21.00, 10, TRUE),
    (2, 8, 11.50, 10, TRUE);

-- Un pedido de ejemplo del cliente María
INSERT INTO Pedidos (usuario_id, direccion_envio_id, metodo_pago_id, zona_envio_id, estado, subtotal, coste_envio, descuento, total) VALUES
    (2, 1, 1, 1, 'entregado', 79.90, 4.95, 0.00, 84.85);

INSERT INTO LineasPedido (pedido_id, producto_id, cantidad, precio_unitario, subtotal) VALUES
    (1, 1, 1, 49.95, 49.95),
    (1, 3, 1, 12.50, 12.50),
    (1, 4, 1, 24.95, 24.95);

-- Una reseña verificada
INSERT INTO Resenas (usuario_id, producto_id, valoracion, texto, verificada) VALUES
    (2, 1, 5, 'A mi perro le encanta esta comida. Llegó muy rápido y bien embalado.', TRUE);

-- =====================================================================
-- VISTAS ÚTILES PARA INFORMES
-- =====================================================================

-- Stock bajo mínimos (alerta para el admin)
CREATE VIEW v_stock_bajo AS
SELECT p.id, p.nombre, p.stock, p.stock_minimo,
       (SELECT pr.nombre FROM Proveedores pr
        JOIN ProductosProveedor pp ON pp.proveedor_id = pr.id
        WHERE pp.producto_id = p.id AND pp.es_principal = TRUE LIMIT 1) AS proveedor_principal
FROM Productos p
WHERE p.activo = TRUE AND p.stock <= p.stock_minimo;

-- Productos más vendidos
CREATE VIEW v_productos_mas_vendidos AS
SELECT p.id, p.nombre, SUM(lp.cantidad) AS unidades_vendidas, SUM(lp.subtotal) AS ingresos
FROM Productos p
JOIN LineasPedido lp ON lp.producto_id = p.id
JOIN Pedidos pe ON pe.id = lp.pedido_id
WHERE pe.estado IN ('pagado', 'preparando', 'enviado', 'entregado')
GROUP BY p.id, p.nombre
ORDER BY unidades_vendidas DESC;

-- Ventas por mes
CREATE VIEW v_ventas_por_mes AS
SELECT DATE_FORMAT(fecha, '%Y-%m') AS mes,
       COUNT(*) AS num_pedidos,
       SUM(total) AS ingresos_totales
FROM Pedidos
WHERE estado IN ('pagado', 'preparando', 'enviado', 'entregado')
GROUP BY mes
ORDER BY mes DESC;

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================