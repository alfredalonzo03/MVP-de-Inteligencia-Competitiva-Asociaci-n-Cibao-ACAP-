"""
Stored Procedures — Competitive Intelligence ACAP
Implementa procedimientos de base de datos como funciones Python
que ejecutan SQL directamente sobre SQLite.

En produccion con PostgreSQL, cada funcion se migraria a PL/pgSQL:
  CREATE OR REPLACE PROCEDURE daily_refresh() LANGUAGE plpgsql AS $$...$$;
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]  # sql/procedures/ -> sql/ -> project root
DB_PATH = ROOT / "data" / "processed" / "competitive_intelligence.db"


def get_connection() -> sqlite3.Connection:
    """Retorna una conexion a la base de datos con row_factory configurado."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── SP_01: Daily Refresh ──────────────────────────────────────────────────────

def sp_daily_refresh() -> dict:
    """
    Refresca todos los datasets corriendo el pipeline ETL completo.
    Equivalente PostgreSQL:
        CREATE PROCEDURE daily_refresh() LANGUAGE plpgsql AS $$
        BEGIN
            PERFORM etl_extract(); PERFORM etl_transform(); PERFORM etl_load();
        END; $$;

    Returns:
        Dict con conteo de filas por tabla actualizada.
    """
    logger.info("[SP] daily_refresh — iniciando...")

    # Importar aqui para evitar circular imports
    from src.etl.pipeline import run_pipeline
    datasets = run_pipeline()

    summary = {name: len(df) for name, df in datasets.items()}
    logger.info("[SP] daily_refresh — completado: %s", summary)
    return summary


# ── SP_02: Competitive Snapshot ───────────────────────────────────────────────

def sp_competitive_snapshot(producto: str = None) -> pd.DataFrame:
    """
    Genera snapshot de tasas actuales: ACAP vs. cada competidor.
    Equivalente PostgreSQL:
        CREATE FUNCTION competitive_snapshot(p_producto TEXT DEFAULT NULL)
        RETURNS TABLE(...) LANGUAGE plpgsql AS $$...$$;

    Args:
        producto: Filtrar por producto especifico. None = todos.

    Returns:
        DataFrame con columnas [producto, institucion, tasa_activa,
        acap_tasa, diferencia_vs_acap, posicion].
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM vw_competitive_snapshot"
        params = []
        if producto:
            query += " WHERE producto = ?"
            params.append(producto)

        df = pd.read_sql_query(query, conn, params=params)

        # Agregar columna de posicion competitiva
        df["posicion"] = df["diferencia_vs_acap"].apply(
            lambda x: "mas_caro" if x > 0.5
            else "mas_barato" if x < -0.5
            else "paridad"
            if x is not None else None
        )
        return df
    finally:
        conn.close()


# ── SP_03: Market Position Report ────────────────────────────────────────────

def sp_market_position_report() -> pd.DataFrame:
    """
    Reporte de posicion estrategica de ACAP en cada segmento.
    Equivalente PostgreSQL:
        CREATE FUNCTION market_position_report()
        RETURNS TABLE(...) LANGUAGE sql AS $$
            SELECT * FROM vw_acap_market_position;
        $$;
    """
    conn = get_connection()
    try:
        return pd.read_sql_query("SELECT * FROM vw_acap_market_position", conn)
    finally:
        conn.close()


# ── SP_04: Alert Monitor ──────────────────────────────────────────────────────

def sp_alert_monitor(dias: int = 90, solo_alto_impacto: bool = False) -> pd.DataFrame:
    """
    Monitorea eventos competitivos recientes y genera alertas.
    Equivalente PostgreSQL:
        CREATE PROCEDURE alert_monitor(p_dias INT, p_solo_alto BOOL)
        LANGUAGE plpgsql AS $$...$$;

    Args:
        dias: Ventana de tiempo en dias hacia atras.
        solo_alto_impacto: Si True, retorna solo eventos de impacto Alto.

    Returns:
        DataFrame con alertas ordenadas por impacto y fecha.
    """
    conn = get_connection()
    try:
        query = """
            SELECT fecha, institucion, tipo_evento, descripcion, impacto_estimado
            FROM competitive_events
            WHERE fecha >= DATE('now', ? || ' days')
              AND impacto_estimado IN ({placeholders})
            ORDER BY
                CASE impacto_estimado WHEN 'Alto' THEN 1 WHEN 'Medio' THEN 2 ELSE 3 END,
                fecha DESC
        """.format(
            placeholders="'Alto'" if solo_alto_impacto else "'Alto', 'Medio'"
        )

        df = pd.read_sql_query(query, conn, params=[f"-{dias}"])
        logger.info("[SP] alert_monitor — %d alertas encontradas (%d dias)", len(df), dias)
        return df
    finally:
        conn.close()


# ── SP_05: Rate Change Trigger ────────────────────────────────────────────────

def sp_detect_rate_changes(threshold_pct: float = 0.5) -> pd.DataFrame:
    """
    Detecta cambios significativos de tasa entre los dos ultimos periodos.
    Simula un TRIGGER de base de datos que se dispara al insertar nuevas tasas.
    Equivalente PostgreSQL:
        CREATE TRIGGER trg_rate_change
        AFTER INSERT ON product_rates
        FOR EACH ROW EXECUTE FUNCTION notify_rate_change();

    Args:
        threshold_pct: Cambio minimo (puntos porcentuales) para generar alerta.

    Returns:
        DataFrame con cambios detectados.
    """
    conn = get_connection()
    try:
        query = """
            WITH ranked AS (
                SELECT
                    institucion, producto, fecha, tasa_activa,
                    LAG(tasa_activa) OVER (
                        PARTITION BY institucion, producto
                        ORDER BY fecha
                    ) AS tasa_anterior
                FROM product_rates
                WHERE tasa_activa IS NOT NULL
            )
            SELECT
                institucion,
                producto,
                fecha,
                ROUND(tasa_anterior, 4)                     AS tasa_anterior,
                ROUND(tasa_activa, 4)                       AS tasa_actual,
                ROUND(tasa_activa - tasa_anterior, 4)       AS cambio_pct,
                CASE
                    WHEN tasa_activa - tasa_anterior > ?  THEN 'SUBE'
                    WHEN tasa_activa - tasa_anterior < -? THEN 'BAJA'
                END AS direccion
            FROM ranked
            WHERE ABS(tasa_activa - tasa_anterior) >= ?
              AND tasa_anterior IS NOT NULL
            ORDER BY ABS(tasa_activa - tasa_anterior) DESC
            LIMIT 50
        """
        df = pd.read_sql_query(
            query, conn,
            params=[threshold_pct, threshold_pct, threshold_pct]
        )
        logger.info("[SP] detect_rate_changes — %d cambios >= %.2f%%", len(df), threshold_pct)
        return df
    finally:
        conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Aplicar schema (crear VIEWs) antes de consultar
    schema_path = ROOT / "sql" / "schema.sql"
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    print("Schema aplicado OK\n")

    print("=== SP_02: Competitive Snapshot (prestamo_personal) ===")
    df = sp_competitive_snapshot("prestamo_personal")
    print(df[["institucion", "tasa_activa", "acap_tasa", "diferencia_vs_acap", "posicion"]].to_string(index=False))

    print("\n=== SP_03: Market Position Report ===")
    df = sp_market_position_report()
    print(df.to_string(index=False))

    print("\n=== SP_04: Alert Monitor (ultimos 90 dias) ===")
    df = sp_alert_monitor(dias=90)
    print(df.head(10).to_string(index=False))

    print("\n=== SP_05: Rate Change Detection (threshold 0.5%) ===")
    df = sp_detect_rate_changes(threshold_pct=0.5)
    print(df.head(10).to_string(index=False))
