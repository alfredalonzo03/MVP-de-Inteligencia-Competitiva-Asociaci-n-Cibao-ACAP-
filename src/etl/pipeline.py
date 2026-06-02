"""
ETL Pipeline — Competitive Intelligence ACAP
Orquesta la extraccion, transformacion y carga de todos los datasets
en la base de datos SQLite local y exporta CSVs para Power BI.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

# Scrapers
from src.scrapers.bcrd_connector import generate_indicators
from src.scrapers.competitor_data import (
    generate_institution_profiles,
    generate_product_rates,
    generate_market_share,
    generate_customer_segments,
    generate_competitive_events,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "processed" / "competitive_intelligence.db"
CSV_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw"


# ── Extract ───────────────────────────────────────────────────────────────────

def extract() -> dict[str, pd.DataFrame]:
    """Extrae datos de todas las fuentes y retorna un diccionario de DataFrames."""
    logger.info("=== EXTRACT ===")
    datasets = {}

    logger.info("Extrayendo indicadores BCRD...")
    datasets["bcrd_indicators"] = generate_indicators(months=24)
    datasets["bcrd_indicators"] = datasets["bcrd_indicators"].reset_index()

    logger.info("Extrayendo perfiles institucionales...")
    datasets["institution_profiles"] = generate_institution_profiles()

    logger.info("Extrayendo tasas por producto (24 meses)...")
    datasets["product_rates"] = generate_product_rates(months=24)

    logger.info("Extrayendo participacion de mercado...")
    datasets["market_share"] = generate_market_share()

    logger.info("Extrayendo segmentos de clientes...")
    datasets["customer_segments"] = generate_customer_segments()

    logger.info("Extrayendo eventos competitivos...")
    datasets["competitive_events"] = generate_competitive_events()

    for name, df in datasets.items():
        logger.info("  %-25s  %d filas x %d columnas", name, len(df), len(df.columns))

    return datasets


# ── Transform ─────────────────────────────────────────────────────────────────

def transform(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Aplica limpieza, tipado y enriquecimiento a cada dataset."""
    logger.info("=== TRANSFORM ===")

    # BCRD: asegurar tipos correctos
    df = datasets["bcrd_indicators"].copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    datasets["bcrd_indicators"] = df

    # Tasas por producto: tipos y columna de spread
    df = datasets["product_rates"].copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    # Marcar si es ACAP o competidor
    df["es_acap"] = df["institucion"] == "Asociación Cibao (ACAP)"
    datasets["product_rates"] = df

    # Participacion: calcular posicion relativa de ACAP por segmento
    df = datasets["market_share"].copy()
    df["rank_segmento"] = (
        df.groupby("segmento")["participacion_pct"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )
    df["vs_lider_pct"] = df.groupby("segmento")["participacion_pct"].transform(
        lambda x: x - x.max()
    )
    datasets["market_share"] = df

    # Clientes: agregar etiqueta de segmento RFM simplificado
    df = datasets["customer_segments"].copy()
    df["valor_cliente"] = pd.cut(
        df["ingreso_mensual_dop"],
        bins=[0, 30_000, 80_000, 200_000, float("inf")],
        labels=["Basico", "Estandar", "Premium", "VIP"],
    )
    datasets["customer_segments"] = df

    # Eventos: convertir fecha y ordenar
    df = datasets["competitive_events"].copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha", ascending=False).reset_index(drop=True)
    datasets["competitive_events"] = df

    for name, df in datasets.items():
        logger.info("  %-25s  transformado OK", name)

    return datasets


# ── Load ──────────────────────────────────────────────────────────────────────

def load(datasets: dict[str, pd.DataFrame]) -> None:
    """Carga los datasets en SQLite y exporta CSVs para Power BI."""
    logger.info("=== LOAD ===")

    # Crear directorios si no existen
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        for table_name, df in datasets.items():
            # Convertir columnas datetime a string para SQLite
            df_to_load = df.copy()
            for col in df_to_load.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
                df_to_load[col] = df_to_load[col].dt.strftime("%Y-%m-%d")

            df_to_load.to_sql(table_name, conn, if_exists="replace", index=False)
            logger.info("  Tabla %-25s  cargada (%d filas)", table_name, len(df_to_load))

        conn.commit()
        logger.info("Base de datos guardada en: %s", DB_PATH)
    finally:
        conn.close()

    # Exportar CSVs para Power BI
    powerbi_tables = [
        "bcrd_indicators",
        "institution_profiles",
        "product_rates",
        "market_share",
        "competitive_events",
    ]
    for table_name in powerbi_tables:
        csv_path = CSV_DIR / f"{table_name}.csv"
        df = datasets[table_name].copy()
        for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info("  CSV exportado: %s", csv_path.name)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_pipeline() -> dict[str, pd.DataFrame]:
    """Ejecuta el pipeline completo: Extract -> Transform -> Load."""
    logger.info("========================================")
    logger.info("  PIPELINE: Competitive Intelligence ACAP")
    logger.info("========================================")

    datasets = extract()
    datasets = transform(datasets)
    load(datasets)

    logger.info("========================================")
    logger.info("  PIPELINE COMPLETADO")
    logger.info("  DB  : %s", DB_PATH)
    logger.info("  CSVs: %s", CSV_DIR)
    logger.info("========================================")
    return datasets


if __name__ == "__main__":
    run_pipeline()
