-- =============================================================================
-- Schema: Competitive Intelligence ACAP
-- Motor: SQLite (dev) | PostgreSQL compatible en produccion
--
-- Nota sobre stored procedures:
--   SQLite no soporta stored procedures nativas. En produccion con PostgreSQL
--   se migraria cada VIEW a una FUNCTION o PROCEDURE con PL/pgSQL.
--   Los "procedimientos" aqui documentados se ejecutan via Python (ver
--   sql/procedures/) usando sqlite3 directamente.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Indicadores economicos BCRD
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bcrd_indicators (
    fecha               TEXT NOT NULL,          -- ISO 8601: YYYY-MM-DD
    tasa_referencia     REAL,                   -- Tasa politica monetaria (%)
    tasa_prestamos      REAL,                   -- Tasa activa promedio (%)
    tasa_depositos      REAL,                   -- Tasa pasiva promedio (%)
    tipo_cambio_compra  REAL,                   -- DOP/USD compra
    tipo_cambio_venta   REAL,                   -- DOP/USD venta
    inflacion           REAL,                   -- Variacion mensual IPC (%)
    reservas_internac   REAL,                   -- Reservas brutas (millones USD)
    PRIMARY KEY (fecha)
);

CREATE INDEX IF NOT EXISTS idx_bcrd_fecha ON bcrd_indicators(fecha);


-- -----------------------------------------------------------------------------
-- 2. Perfiles institucionales de competidores
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institution_profiles (
    institucion         TEXT NOT NULL PRIMARY KEY,
    tipo                TEXT NOT NULL,          -- Banco Comercial, Estatal, etc.
    tamaño              TEXT,                   -- Grande / Mediano / Pequeno
    sucursales          INTEGER,
    empleados           INTEGER,
    activos_usd_mm      REAL,                   -- Activos en millones USD
    segmentos           TEXT,                   -- Lista separada por coma
    presencia_digital   INTEGER,                -- Score 0-100
    calificacion_riesgo TEXT                    -- AA-, A+, etc.
);


-- -----------------------------------------------------------------------------
-- 3. Tasas de interes por producto e institucion (serie de tiempo)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT NOT NULL,
    institucion     TEXT NOT NULL,
    producto        TEXT NOT NULL,
    tasa_activa     REAL,                       -- Tasa cobrada al cliente (%)
    tasa_pasiva     REAL,                       -- Tasa pagada al cliente (%)
    es_acap         INTEGER DEFAULT 0,          -- 1 si es ACAP, 0 si competidor
    FOREIGN KEY (institucion) REFERENCES institution_profiles(institucion)
);

CREATE INDEX IF NOT EXISTS idx_rates_fecha       ON product_rates(fecha);
CREATE INDEX IF NOT EXISTS idx_rates_institucion ON product_rates(institucion);
CREATE INDEX IF NOT EXISTS idx_rates_producto    ON product_rates(producto);


-- -----------------------------------------------------------------------------
-- 4. Participacion de mercado por segmento
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_share (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    segmento            TEXT NOT NULL,
    institucion         TEXT NOT NULL,
    participacion_pct   REAL NOT NULL,
    year                INTEGER NOT NULL,
    rank_segmento       INTEGER,                -- Posicion dentro del segmento
    vs_lider_pct        REAL,                   -- Diferencia vs. lider (negativo = detras)
    UNIQUE (segmento, institucion, year)
);


-- -----------------------------------------------------------------------------
-- 5. Segmentos de clientes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_segments (
    cliente_id          TEXT PRIMARY KEY,
    edad                INTEGER,
    ingreso_mensual_dop REAL,
    segmento_ingreso    TEXT,                   -- Bajo / Medio / Medio-Alto / Alto
    producto_principal  TEXT,
    nps                 INTEGER,                -- Net Promoter Score (-100 a 100)
    antiguedad_años     INTEGER,
    usuario_digital     INTEGER,                -- 1 = si, 0 = no
    valor_cliente       TEXT                    -- Basico / Estandar / Premium / VIP
);

CREATE INDEX IF NOT EXISTS idx_seg_ingreso  ON customer_segments(segmento_ingreso);
CREATE INDEX IF NOT EXISTS idx_seg_producto ON customer_segments(producto_principal);
CREATE INDEX IF NOT EXISTS idx_seg_valor    ON customer_segments(valor_cliente);


-- -----------------------------------------------------------------------------
-- 6. Eventos competitivos
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS competitive_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha               TEXT NOT NULL,
    institucion         TEXT NOT NULL,
    tipo_evento         TEXT NOT NULL,
    descripcion         TEXT,
    impacto_estimado    TEXT,                   -- Alto / Medio / Bajo
    FOREIGN KEY (institucion) REFERENCES institution_profiles(institucion)
);

CREATE INDEX IF NOT EXISTS idx_events_fecha       ON competitive_events(fecha);
CREATE INDEX IF NOT EXISTS idx_events_institucion ON competitive_events(institucion);
CREATE INDEX IF NOT EXISTS idx_events_impacto     ON competitive_events(impacto_estimado);


-- =============================================================================
-- VIEWS (equivalentes a stored procedures de solo lectura)
-- =============================================================================

-- VW_01: Snapshot competitivo — tasas activas actuales vs. ACAP
CREATE VIEW IF NOT EXISTS vw_competitive_snapshot AS
SELECT
    pr.producto,
    pr.institucion,
    pr.tasa_activa,
    pr.es_acap,
    acap.tasa_activa                            AS acap_tasa,
    ROUND(pr.tasa_activa - acap.tasa_activa, 2) AS diferencia_vs_acap
FROM product_rates pr
JOIN (
    SELECT producto, tasa_activa
    FROM product_rates
    WHERE es_acap = 1
      AND fecha = (SELECT MAX(fecha) FROM product_rates WHERE es_acap = 1)
      AND tasa_activa IS NOT NULL
) acap ON pr.producto = acap.producto
WHERE pr.fecha = (SELECT MAX(fecha) FROM product_rates)
  AND pr.tasa_activa IS NOT NULL
ORDER BY pr.producto, pr.tasa_activa;


-- VW_02: Posicion de mercado de ACAP por segmento
CREATE VIEW IF NOT EXISTS vw_acap_market_position AS
SELECT
    segmento,
    participacion_pct,
    rank_segmento,
    vs_lider_pct,
    CASE
        WHEN rank_segmento = 1 THEN 'Lider'
        WHEN rank_segmento = 2 THEN 'Retador'
        WHEN rank_segmento <= 4 THEN 'Seguidor'
        ELSE 'Nicho'
    END AS posicion_estrategica
FROM market_share
WHERE institucion = 'Asociación Cibao (ACAP)'
ORDER BY rank_segmento;


-- VW_03: Alertas de eventos competitivos recientes (90 dias)
CREATE VIEW IF NOT EXISTS vw_recent_alerts AS
SELECT
    fecha,
    institucion,
    tipo_evento,
    descripcion,
    impacto_estimado
FROM competitive_events
WHERE fecha >= DATE('now', '-90 days')
  AND impacto_estimado IN ('Alto', 'Medio')
ORDER BY
    CASE impacto_estimado WHEN 'Alto' THEN 1 WHEN 'Medio' THEN 2 ELSE 3 END,
    fecha DESC;


-- VW_04: Indicadores macroeconomicos recientes (ultimo año)
CREATE VIEW IF NOT EXISTS vw_macro_trends AS
SELECT
    fecha,
    tasa_referencia,
    tasa_prestamos,
    tasa_depositos,
    tipo_cambio_venta,
    inflacion,
    reservas_internac
FROM bcrd_indicators
WHERE fecha >= DATE('now', '-365 days')
ORDER BY fecha;


-- VW_05: Perfil de cliente promedio por segmento de valor
CREATE VIEW IF NOT EXISTS vw_customer_profile AS
SELECT
    valor_cliente,
    COUNT(*)                            AS total_clientes,
    ROUND(AVG(edad), 1)                 AS edad_promedio,
    ROUND(AVG(ingreso_mensual_dop), 0)  AS ingreso_promedio_dop,
    ROUND(AVG(nps), 1)                  AS nps_promedio,
    ROUND(AVG(antiguedad_años), 1)      AS antiguedad_promedio,
    ROUND(100.0 * SUM(usuario_digital) / COUNT(*), 1) AS pct_digital
FROM customer_segments
GROUP BY valor_cliente
ORDER BY
    CASE valor_cliente
        WHEN 'VIP'      THEN 1
        WHEN 'Premium'  THEN 2
        WHEN 'Estandar' THEN 3
        ELSE 4
    END;
