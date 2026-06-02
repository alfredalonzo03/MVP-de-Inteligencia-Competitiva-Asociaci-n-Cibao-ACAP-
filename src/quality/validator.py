"""
Agency Data Validator
=====================
Orchestrates the full agency data quality pipeline:

  Step 1 — GE Validation (data contract checks)
    Runs each agency report through its Great Expectations suite.
    Catches: schema violations, nulls, out-of-range values,
             wrong formats, duplicates.

  Step 2 — Cross-Validation (agency vs. internal data)
    Compares agency figures against the internal SQLite database.
    Catches: discrepancies in market share (>3pp threshold)
             and reported rates (>2pp threshold).

  Step 3 — Critique Report (output for Power BI)
    Exports data/quality_reports/agency_critique_report.csv
    with all flagged issues, severity, and recommendations.

Run:
    python -m src.quality.validator
"""
from __future__ import annotations

import pandas as pd
import sqlalchemy as sa
import great_expectations as gx
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parents[2]
AGENCY_DIR   = ROOT / "data" / "agency"
REPORTS_DIR  = ROOT / "data" / "quality_reports"
DB_PATH      = ROOT / "data" / "processed" / "competitive_intelligence.db"

INSTITUTION_NAME_MAP = {
    "Asociación Cibao (ACAP)": "Asociación Cibao",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_agency_data() -> dict[str, pd.DataFrame]:
    files = {
        "market_share": "ipsos_market_share.csv",
        "satisfaction":  "kantar_satisfaction.csv",
        "penetration":   "nielsen_penetration.csv",
    }
    return {
        key: pd.read_csv(AGENCY_DIR / fname)
        for key, fname in files.items()
        if (AGENCY_DIR / fname).exists()
    }


def _run_ge_validation(
    df: pd.DataFrame,
    suite: gx.ExpectationSuite,
    context: gx.DataContext,
    datasource_name: str,
) -> object:
    """Attach df to a Pandas datasource and validate against suite."""
    ds   = context.data_sources.add_pandas(name=datasource_name)
    asset = ds.add_dataframe_asset(name="data")
    batch_def = asset.add_batch_definition_whole_dataframe("batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    return batch.validate(suite)


def _parse_ge_results(result, report_name: str) -> list[dict]:
    """Flatten GE result into rows for the critique report."""
    rows = []
    for er in result.results:
        if er.success:
            continue
        cfg = er.expectation_config
        res = er.result
        rows.append({
            "timestamp":           datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente":              report_name,
            "tipo_hallazgo":       "contrato_datos",
            "categoria":           cfg.type,
            "campo":               cfg.kwargs.get("column", "tabla"),
            "valor_incorrecto":    str(res.get("partial_unexpected_list", [])[:5]),
            "registros_afectados": res.get("unexpected_count", 0),
            "pct_afectado":        round(res.get("unexpected_percent", 0.0), 2),
            "severidad":           "Alta" if res.get("unexpected_percent", 0) > 5 else "Media",
            "recomendacion":       (
                f"Contrato violado: '{cfg.type}' en columna '{cfg.kwargs.get('column', 'tabla')}'. "
                f"Solicitar corrección a agencia antes de usar el dato."
            ),
            "accion_requerida":    "Rechazar reporte / Solicitar reenvío corregido",
        })
    return rows


# ── Cross-validation logic ────────────────────────────────────────────────────

def _cross_validate_market_share(agency_df: pd.DataFrame) -> list[dict]:
    """
    Compare Ipsos market share figures vs. internal model.
    Flags rows where |agency - internal| > 3 percentage points.
    """
    if not DB_PATH.exists():
        return []

    engine = sa.create_engine(f"sqlite:///{DB_PATH}")
    try:
        internal = pd.read_sql(
            """
            SELECT institucion, segmento, participacion_pct
            FROM   market_share
            WHERE  fecha = (SELECT MAX(fecha) FROM market_share)
            """,
            engine,
        )
    except Exception:
        return []

    internal["institucion"] = internal["institucion"].replace(INSTITUTION_NAME_MAP)

    # Keep only clean agency rows for cross-validation
    clean = agency_df.dropna(subset=["institucion", "segmento", "cuota_pct"])
    clean = clean[clean["cuota_pct"].between(0, 100)]

    merged = clean.merge(
        internal, on=["institucion", "segmento"], suffixes=("_agency", "_internal"), how="inner"
    )
    merged["delta_pp"] = (merged["cuota_pct"] - merged["participacion_pct"]).abs()

    issues = []
    for _, row in merged[merged["delta_pp"] > 3.0].iterrows():
        issues.append({
            "timestamp":           datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente":              "ipsos_market_share",
            "tipo_hallazgo":       "discrepancia_vs_interno",
            "categoria":           "market_share_gap",
            "campo":               f"{row['institucion']} / {row['segmento']}",
            "valor_incorrecto":    f"Agencia: {row['cuota_pct']}% | Interno: {row['participacion_pct']:.1f}%",
            "registros_afectados": 1,
            "pct_afectado":        None,
            "severidad":           "Alta" if row["delta_pp"] > 5 else "Media",
            "recomendacion":       (
                f"Diferencia de {row['delta_pp']:.1f}pp supera umbral de 3pp para "
                f"{row['segmento']}. Verificar metodología de Ipsos (marco muestral, fecha de corte)."
            ),
            "accion_requerida":    "Investigar con agencia — no usar cifra hasta reconciliar",
        })

    return issues


def _cross_validate_rates(agency_df: pd.DataFrame) -> list[dict]:
    """
    Compare Nielsen reported rates vs. internal product_rates average (last 90 days).
    Flags rows where |agency - internal| > 2 percentage points.
    """
    if not DB_PATH.exists():
        return []

    engine = sa.create_engine(f"sqlite:///{DB_PATH}")
    try:
        internal = pd.read_sql(
            """
            SELECT   institucion, producto, ROUND(AVG(tasa), 2) AS tasa_interna
            FROM     product_rates
            WHERE    fecha >= DATE('now', '-90 days')
            GROUP BY institucion, producto
            """,
            engine,
        )
    except Exception:
        return []

    internal["institucion"] = internal["institucion"].replace(INSTITUTION_NAME_MAP)

    clean = agency_df.dropna(subset=["institucion", "producto", "tasa_promedio_reportada"])
    clean = clean[clean["tasa_promedio_reportada"].between(0, 60)]

    merged = clean.merge(
        internal, on=["institucion", "producto"], how="inner"
    )
    merged["delta_pp"] = (merged["tasa_promedio_reportada"] - merged["tasa_interna"]).abs()

    issues = []
    for _, row in merged[merged["delta_pp"] > 2.0].iterrows():
        issues.append({
            "timestamp":           datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fuente":              "nielsen_penetration",
            "tipo_hallazgo":       "discrepancia_vs_interno",
            "categoria":           "rate_gap",
            "campo":               f"{row['institucion']} / {row['producto']}",
            "valor_incorrecto":    f"Agencia: {row['tasa_promedio_reportada']}% | Interno: {row['tasa_interna']}%",
            "registros_afectados": 1,
            "pct_afectado":        None,
            "severidad":           "Alta" if row["delta_pp"] > 5 else "Media",
            "recomendacion":       (
                f"Delta de {row['delta_pp']:.1f}pp entre Nielsen y datos internos para "
                f"'{row['producto']}' en {row['institucion']}. "
                f"Posible diferencia en metodología de cálculo de tasa efectiva."
            ),
            "accion_requerida":    "Verificar con fuente primaria (publicaciones SB/BCRD)",
        })

    return issues


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_validation() -> pd.DataFrame:
    """
    Run the full agency data quality pipeline.
    Returns a DataFrame with all flagged issues, ready for Power BI.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 62)
    print("  AGENCY DATA VALIDATOR — Inteligencia Competitiva ACAP")
    print("=" * 62)

    # ── Step 1: Load agency data ──────────────────────────────────────
    dfs = _load_agency_data()
    if not dfs:
        print("\n  [ERROR] No agency files found. Run agency_data_generator.py first.")
        return pd.DataFrame()

    print(f"\n  Loaded {len(dfs)} agency reports from {AGENCY_DIR.relative_to(ROOT)}/")

    # ── Step 2: GE validation ─────────────────────────────────────────
    from src.quality.data_contract import (
        build_market_share_suite,
        build_satisfaction_suite,
        build_penetration_suite,
    )

    context = gx.get_context(mode="ephemeral")

    suite_config = {
        "market_share": (build_market_share_suite, "Ipsos RD"),
        "satisfaction":  (build_satisfaction_suite,  "Kantar BrandZ"),
        "penetration":   (build_penetration_suite,   "Nielsen Financial RD"),
    }

    all_findings: list[dict] = []

    print("\n  ── GE Contract Validation ──────────────────────────────")
    for key, (build_fn, label) in suite_config.items():
        if key not in dfs:
            print(f"  [{key.upper():14s}] SKIPPED — file not found")
            continue

        df    = dfs[key]
        suite = build_fn(context)
        result = _run_ge_validation(df, suite, context, datasource_name=f"ds_{key}")
        failures = _parse_ge_results(result, key)
        all_findings.extend(failures)

        stats = result.statistics
        evaluated = stats["evaluated_expectations"]
        passed    = stats["successful_expectations"]
        failed    = stats["unsuccessful_expectations"]
        pass_rate = passed / evaluated * 100 if evaluated else 0

        status = "✅ PASS" if failed == 0 else f"❌ {failed} FAIL"
        print(f"\n  [{label}]")
        print(f"    Expectations : {evaluated} evaluated  |  {passed} passed  |  {failed} failed")
        print(f"    Pass rate    : {pass_rate:.0f}%  {status}")
        if failures:
            for f in failures:
                print(f"    ⚠  {f['campo']}: {f['categoria']} ({f['pct_afectado']}% rows affected)")

    # ── Step 3: Cross-validation vs. internal data ────────────────────
    print("\n  ── Cross-Validation vs. Internal Database ──────────────")

    ms_issues = _cross_validate_market_share(dfs.get("market_share", pd.DataFrame()))
    all_findings.extend(ms_issues)
    print(f"  Market share discrepancies (>3pp) : {len(ms_issues)}")

    rate_issues = _cross_validate_rates(dfs.get("penetration", pd.DataFrame()))
    all_findings.extend(rate_issues)
    print(f"  Rate discrepancies (>2pp)         : {len(rate_issues)}")

    # ── Step 4: Build & export critique report ────────────────────────
    columns = [
        "timestamp", "fuente", "tipo_hallazgo", "categoria", "campo",
        "valor_incorrecto", "registros_afectados", "pct_afectado",
        "severidad", "recomendacion", "accion_requerida",
    ]

    if all_findings:
        critique_df = pd.DataFrame(all_findings, columns=columns)
    else:
        critique_df = pd.DataFrame(columns=columns)

    report_path = REPORTS_DIR / "agency_critique_report.csv"
    critique_df.to_csv(report_path, index=False)

    print("\n  ── Summary ─────────────────────────────────────────────")
    print(f"  Total issues flagged : {len(critique_df)}")
    if len(critique_df) > 0:
        for sev, grp in critique_df.groupby("severidad"):
            print(f"    {sev:6s} : {len(grp)}")
        for tipo, grp in critique_df.groupby("tipo_hallazgo"):
            print(f"    {tipo:35s}: {len(grp)}")

    print(f"\n  Report saved → {report_path.relative_to(ROOT)}")
    print("=" * 62)

    return critique_df


if __name__ == "__main__":
    from src.quality.agency_data_generator import save_agency_reports

    print("Generating synthetic agency reports...\n")
    save_agency_reports()

    print()
    run_validation()
