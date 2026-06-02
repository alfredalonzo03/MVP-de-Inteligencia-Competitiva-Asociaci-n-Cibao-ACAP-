"""
Competitive Analysis — Análisis de posicionamiento competitivo de ACAP
Genera métricas comparativas, rankings y oportunidades estratégicas.
"""

import sqlite3
import logging
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "processed" / "competitive_intelligence.db"
CSV_DIR = ROOT / "data" / "processed"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── 1. Pricing Competitiveness ────────────────────────────────────────────────

def pricing_competitiveness() -> pd.DataFrame:
    """
    Para cada producto calcula si ACAP es competitivo frente al mercado.

    Returns:
        DataFrame con columnas:
        [producto, acap_tasa, mercado_min, mercado_max, mercado_promedio,
         diferencia_vs_promedio, diferencia_vs_minimo, competitividad]
    """
    conn = _get_conn()
    df = pd.read_sql_query(
        """
        SELECT producto, institucion, tasa_activa, es_acap
        FROM product_rates
        WHERE fecha = (SELECT MAX(fecha) FROM product_rates)
          AND tasa_activa IS NOT NULL
        """,
        conn,
    )
    conn.close()

    acap = df[df["es_acap"] == 1][["producto", "tasa_activa"]].rename(
        columns={"tasa_activa": "acap_tasa"}
    )
    market = (
        df[df["es_acap"] == 0]
        .groupby("producto")["tasa_activa"]
        .agg(mercado_min="min", mercado_max="max", mercado_promedio="mean")
        .reset_index()
    )

    result = acap.merge(market, on="producto", how="inner")
    result["diferencia_vs_promedio"] = (
        result["acap_tasa"] - result["mercado_promedio"]
    ).round(2)
    result["diferencia_vs_minimo"] = (
        result["acap_tasa"] - result["mercado_min"]
    ).round(2)
    result["mercado_promedio"] = result["mercado_promedio"].round(2)
    result["mercado_min"] = result["mercado_min"].round(2)
    result["mercado_max"] = result["mercado_max"].round(2)
    result["acap_tasa"] = result["acap_tasa"].round(2)

    # Clasificar competitividad
    result["competitividad"] = result["diferencia_vs_promedio"].apply(
        lambda d: "Competitivo" if d <= -0.5
        else "No competitivo" if d >= 1.0
        else "Paridad"
    )

    return result.sort_values("diferencia_vs_promedio", ascending=False)


# ── 2. Market Share Trends ────────────────────────────────────────────────────

def market_opportunity_gaps() -> pd.DataFrame:
    """
    Identifica segmentos donde ACAP tiene mayor brecha con el líder
    y donde hay mayor potencial de crecimiento.

    Returns:
        DataFrame con posicion de ACAP y oportunidad estimada por segmento.
    """
    conn = _get_conn()
    df = pd.read_sql_query("SELECT * FROM market_share", conn)
    conn.close()

    acap = df[df["institucion"] == "Asociación Cibao (ACAP)"].copy()
    leader = (
        df.groupby("segmento")["participacion_pct"]
        .max()
        .reset_index()
        .rename(columns={"participacion_pct": "lider_pct"})
    )
    market_total = (
        df.groupby("segmento")["participacion_pct"]
        .sum()
        .reset_index()
        .rename(columns={"participacion_pct": "total_mercado_pct"})
    )

    result = acap[["segmento", "participacion_pct", "rank_segmento", "vs_lider_pct"]].merge(
        leader, on="segmento"
    ).merge(market_total, on="segmento")

    # Oportunidad: si ACAP cierra la mitad de la brecha con el líder
    result["oportunidad_crecimiento_pct"] = (
        (result["lider_pct"] - result["participacion_pct"]) / 2
    ).round(1)

    result["prioridad"] = result.apply(
        lambda r: "Alta" if r["oportunidad_crecimiento_pct"] > 8
        else "Media" if r["oportunidad_crecimiento_pct"] > 4
        else "Baja",
        axis=1,
    )

    return result.sort_values("oportunidad_crecimiento_pct", ascending=False)


# ── 3. Competitor Profile Matrix ──────────────────────────────────────────────

def competitor_profile_matrix() -> pd.DataFrame:
    """
    Construye una matriz de perfiles de competidores normalizada
    para comparación visual.

    Returns:
        DataFrame con score normalizado [0-100] por dimensión.
    """
    conn = _get_conn()
    df = pd.read_sql_query("SELECT * FROM institution_profiles", conn)
    conn.close()

    numeric_cols = ["sucursales", "empleados", "activos_usd_mm", "presencia_digital"]
    matrix = df[["institucion", "tipo"] + numeric_cols].copy()

    # Normalizar 0-100 por columna
    for col in numeric_cols:
        col_min = matrix[col].min()
        col_max = matrix[col].max()
        if col_max > col_min:
            matrix[f"{col}_score"] = (
                (matrix[col] - col_min) / (col_max - col_min) * 100
            ).round(1)
        else:
            matrix[f"{col}_score"] = 50.0

    # Score compuesto
    score_cols = [f"{c}_score" for c in numeric_cols]
    matrix["score_total"] = matrix[score_cols].mean(axis=1).round(1)
    matrix = matrix.sort_values("score_total", ascending=False)

    return matrix[["institucion", "tipo"] + score_cols + ["score_total"]]


# ── 4. Rate Trend Analysis ────────────────────────────────────────────────────

def rate_trend_analysis(producto: str = "prestamo_personal") -> pd.DataFrame:
    """
    Analiza la evolución de tasas de ACAP vs. promedio de mercado
    en los últimos 12 meses para un producto dado.

    Args:
        producto: Nombre del producto a analizar.

    Returns:
        DataFrame mensual con [fecha, acap_tasa, mercado_promedio, spread].
    """
    conn = _get_conn()
    df = pd.read_sql_query(
        """
        SELECT fecha, es_acap, AVG(tasa_activa) AS tasa_activa
        FROM product_rates
        WHERE producto = ?
          AND tasa_activa IS NOT NULL
          AND fecha >= DATE('now', '-365 days')
        GROUP BY fecha, es_acap
        ORDER BY fecha
        """,
        conn,
        params=[producto],
    )
    conn.close()

    df["fecha"] = pd.to_datetime(df["fecha"])
    acap_df = df[df["es_acap"] == 1][["fecha", "tasa_activa"]].rename(
        columns={"tasa_activa": "acap_tasa"}
    )
    market_df = df[df["es_acap"] == 0][["fecha", "tasa_activa"]].rename(
        columns={"tasa_activa": "mercado_promedio"}
    )

    result = acap_df.merge(market_df, on="fecha", how="inner")
    result["spread"] = (result["acap_tasa"] - result["mercado_promedio"]).round(3)
    result["acap_tasa"] = result["acap_tasa"].round(3)
    result["mercado_promedio"] = result["mercado_promedio"].round(3)
    return result


# ── 5. Export para Power BI ───────────────────────────────────────────────────

def export_analysis_csvs() -> None:
    """Exporta todos los análisis como CSVs para Power BI."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    exports = {
        "analysis_pricing":       pricing_competitiveness(),
        "analysis_market_gaps":   market_opportunity_gaps(),
        "analysis_competitor_matrix": competitor_profile_matrix(),
        "analysis_rate_trend":    rate_trend_analysis(),
    }

    for name, df in exports.items():
        path = CSV_DIR / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info("Exportado: %s (%d filas)", path.name, len(df))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("=== 1. Pricing Competitiveness ===")
    df = pricing_competitiveness()
    print(df[["producto", "acap_tasa", "mercado_promedio",
              "diferencia_vs_promedio", "competitividad"]].to_string(index=False))

    print("\n=== 2. Market Opportunity Gaps ===")
    df = market_opportunity_gaps()
    print(df[["segmento", "participacion_pct", "rank_segmento",
              "oportunidad_crecimiento_pct", "prioridad"]].to_string(index=False))

    print("\n=== 3. Competitor Profile Matrix ===")
    df = competitor_profile_matrix()
    print(df[["institucion", "score_total"]].to_string(index=False))

    print("\n=== 4. Rate Trend (prestamo_personal, ultimos 12 meses) ===")
    df = rate_trend_analysis("prestamo_personal")
    print(df.tail(6).to_string(index=False))

    print("\n=== Exportando CSVs de análisis... ===")
    export_analysis_csvs()
    print("Listo.")
