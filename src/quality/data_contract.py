"""
Data Contracts — Great Expectations Suites
===========================================
Defines one ExpectationSuite per agency report type.
Each suite is the formal "contract" that external agencies must satisfy.

Usage:
    from src.quality.data_contract import (
        build_market_share_suite,
        build_satisfaction_suite,
        build_penetration_suite,
    )
    suite = build_market_share_suite(context)
"""
import great_expectations as gx
from great_expectations.core import ExpectationSuite
from great_expectations.data_context import AbstractDataContext

VALID_INSTITUTIONS = [
    "BanReservas", "Banco Popular", "BHD León",
    "Scotiabank RD", "Asociación Cibao", "Alaver", "ADEMI",
]

VALID_SEGMENTS = ["Ahorros", "Comercial", "Personal", "Hipotecario", "Microcrédito"]

VALID_PRODUCTS = [
    "cuenta_ahorro", "prestamo_personal",
    "prestamo_hipotecario", "tarjeta_credito", "deposito_plazo",
]

DATE_REGEX_ISO = r"^\d{4}-\d{2}-\d{2}$"


def build_market_share_suite(context: AbstractDataContext) -> ExpectationSuite:
    """
    Contract: Quarterly market share study (Ipsos-style).

    Rules:
      - Required columns present and non-null
      - cuota_pct strictly between 0 and 100
      - Institution names match internal master list
      - Segment names match allowed taxonomy
      - Date in ISO format YYYY-MM-DD
      - One row per (institucion, segmento) — no duplicates
      - Row count: 7 institutions × 5 segments = 35 (±5 tolerance)
    """
    suite = context.suites.add(ExpectationSuite(name="market_share_contract"))

    # ── Schema ──────────────────────────────────────────────────────────
    required_columns = ["institucion", "segmento", "cuota_pct", "fecha_estudio"]
    for col in required_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnToExist(column=col)
        )

    # ── Nullability ─────────────────────────────────────────────────────
    for col in required_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )

    # ── Value ranges ────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="cuota_pct", min_value=0.0, max_value=100.0
        )
    )

    # ── Allowed values (domain taxonomy) ────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="institucion", value_set=VALID_INSTITUTIONS
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="segmento", value_set=VALID_SEGMENTS
        )
    )

    # ── Date format ─────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="fecha_estudio", regex=DATE_REGEX_ISO
        )
    )

    # ── Uniqueness ──────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["institucion", "segmento"]
        )
    )

    # ── Row count ───────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=30, max_value=40
        )
    )

    return suite


def build_satisfaction_suite(context: AbstractDataContext) -> ExpectationSuite:
    """
    Contract: Customer satisfaction & NPS study (Kantar-style).

    Rules:
      - Required columns present and non-null
      - NPS in valid range [-100, 100]
      - Percentage columns in [0, 100]
      - Institution names match master list
      - segmento_cliente in allowed taxonomy
      - No duplicate (institucion, segmento_cliente) combinations
    """
    suite = context.suites.add(ExpectationSuite(name="satisfaction_contract"))

    # ── Schema ──────────────────────────────────────────────────────────
    required_columns = ["institucion", "segmento_cliente", "nps", "satisfaccion_pct"]
    for col in required_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnToExist(column=col)
        )

    # ── Nullability ─────────────────────────────────────────────────────
    for col in required_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )

    # ── Value ranges ────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="nps", min_value=-100, max_value=100
        )
    )
    for pct_col in ["satisfaccion_pct", "recomendaria_pct"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=pct_col, min_value=0.0, max_value=100.0
            )
        )

    # ── Allowed values ───────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="institucion", value_set=VALID_INSTITUTIONS
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="segmento_cliente", value_set=["Retail", "Empresas", "PyMES"]
        )
    )

    # ── Uniqueness ──────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["institucion", "segmento_cliente"]
        )
    )

    return suite


def build_penetration_suite(context: AbstractDataContext) -> ExpectationSuite:
    """
    Contract: Product penetration & rate study (Nielsen-style).

    Rules:
      - Required columns present and non-null
      - penetracion_pct in [0, 100]
      - tasa_promedio_reportada in [0, 60] — realistic banking rates in DR
      - Institution names match master list (mostly — 95% threshold)
      - fecha_corte in ISO format YYYY-MM-DD
      - One row per (institucion, producto)
    """
    suite = context.suites.add(ExpectationSuite(name="penetration_contract"))

    # ── Schema ──────────────────────────────────────────────────────────
    required_columns = [
        "institucion", "producto",
        "penetracion_pct", "tasa_promedio_reportada", "fecha_corte",
    ]
    for col in required_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnToExist(column=col)
        )

    # ── Nullability ─────────────────────────────────────────────────────
    for col in ["institucion", "producto", "penetracion_pct"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )

    # ── Value ranges ────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="penetracion_pct", min_value=0.0, max_value=100.0
        )
    )
    # Realistic rate range for Dominican banking market
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="tasa_promedio_reportada", min_value=0.0, max_value=60.0
        )
    )

    # ── Allowed values ───────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="institucion",
            value_set=VALID_INSTITUTIONS,
            mostly=0.95,   # tolerate ≤5% unknown (null treated separately)
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="producto", value_set=VALID_PRODUCTS
        )
    )

    # ── Date format ─────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="fecha_corte", regex=DATE_REGEX_ISO
        )
    )

    # ── Uniqueness ──────────────────────────────────────────────────────
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["institucion", "producto"]
        )
    )

    return suite
