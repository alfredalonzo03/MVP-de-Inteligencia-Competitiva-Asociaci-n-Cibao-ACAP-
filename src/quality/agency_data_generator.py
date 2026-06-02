"""
Agency Data Generator
=====================
Simulates receiving market research reports from 3 external agencies.
Each report intentionally contains realistic data quality issues to
demonstrate the value of automated contract validation.

Agencies simulated:
  - Ipsos RD        → Quarterly market share study
  - Kantar BrandZ   → Customer satisfaction & NPS study
  - Nielsen RD      → Product penetration & rate study
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parents[2]
AGENCY_DIR = ROOT / "data" / "agency"

VALID_INSTITUTIONS = [
    "BanReservas", "Banco Popular", "BHD León",
    "Scotiabank RD", "Asociación Cibao", "Alaver", "ADEMI",
]

SEGMENTS = ["Ahorros", "Comercial", "Personal", "Hipotecario", "Microcrédito"]

PRODUCTS = [
    "cuenta_ahorro", "prestamo_personal",
    "prestamo_hipotecario", "tarjeta_credito", "deposito_plazo",
]

# Base market shares per segment (should sum ~100 per segment)
BASE_SHARES = {
    "BanReservas":      [28, 25, 28, 24, 20],
    "Banco Popular":    [24, 24, 24, 20, 17],
    "BHD León":         [14, 18, 10, 20, 10],
    "Scotiabank RD":    [10,  6,  6, 15,  6],
    "Asociación Cibao": [14, 10, 10, 15, 10],
    "Alaver":           [ 6,  9, 14,  5, 16],
    "ADEMI":            [ 4,  8,  8,  1, 21],
}

# Base NPS and satisfaction values
BASE_SATISFACTION = {
    "BanReservas":      {"retail_nps": 45, "retail_sat": 78, "corp_nps": 48, "corp_sat": 80},
    "Banco Popular":    {"retail_nps": 38, "retail_sat": 72, "corp_nps": 42, "corp_sat": 75},
    "BHD León":         {"retail_nps": 52, "retail_sat": 81, "corp_nps": 55, "corp_sat": 83},
    "Scotiabank RD":    {"retail_nps": 41, "retail_sat": 74, "corp_nps": 44, "corp_sat": 76},
    "Asociación Cibao": {"retail_nps": 35, "retail_sat": 68, "corp_nps": 33, "corp_sat": 65},
    "Alaver":           {"retail_nps": 28, "retail_sat": 62, "corp_nps": 30, "corp_sat": 63},
    "ADEMI":            {"retail_nps": 31, "retail_sat": 65, "corp_nps": 29, "corp_sat": 62},
}


def generate_ipsos_market_share(seed: int = 42) -> pd.DataFrame:
    """
    Ipsos RD — Quarterly Market Share Study (Q1 2026).

    Intentional data quality issues introduced:
      1. Institution name typo: 'ADEMI' → 'Ademi S.A.' (fails allowed-values contract)
      2. cuota_pct = 128.5 for BanReservas/Ahorros (fails 0–100 range contract)
      3. Missing fecha_estudio for Alaver/Microcrédito (fails not-null contract)
    """
    np.random.seed(seed)
    rows = []
    for inst, shares in BASE_SHARES.items():
        for i, seg in enumerate(SEGMENTS):
            rows.append({
                "institucion": inst,
                "segmento": seg,
                "cuota_pct": round(shares[i] + np.random.uniform(-0.5, 0.5), 2),
                "fecha_estudio": "2026-03-31",
                "metodologia": "Panel presencial 1,200 personas",
                "margen_error_pct": 2.1,
                "fuente": "Ipsos RD",
            })

    df = pd.DataFrame(rows)

    # --- Issue 1: Institution name typo ---
    df.loc[df["institucion"] == "ADEMI", "institucion"] = "Ademi S.A."

    # --- Issue 2: cuota_pct out of range ---
    mask = (df["institucion"] == "BanReservas") & (df["segmento"] == "Ahorros")
    df.loc[mask, "cuota_pct"] = 128.5

    # --- Issue 3: Missing date ---
    mask = (df["institucion"] == "Alaver") & (df["segmento"] == "Microcrédito")
    df.loc[mask, "fecha_estudio"] = None

    return df


def generate_kantar_satisfaction(seed: int = 42) -> pd.DataFrame:
    """
    Kantar BrandZ — Customer Satisfaction & NPS Study (Q1 2026).

    Intentional data quality issues introduced:
      1. NPS = 155 for BHD León/Empresas (fails -100 to 100 range contract)
      2. satisfaccion_pct = 102.3 for Banco Popular (fails 0–100 range contract)
      3. Duplicate row for BanReservas/Retail (fails compound uniqueness contract)
    """
    np.random.seed(seed)
    rows = []
    for inst, vals in BASE_SATISFACTION.items():
        rows.append({
            "institucion": inst,
            "segmento_cliente": "Retail",
            "nps": vals["retail_nps"] + np.random.randint(-2, 3),
            "satisfaccion_pct": round(vals["retail_sat"] + np.random.uniform(-1, 1), 1),
            "recomendaria_pct": round(vals["retail_sat"] + np.random.uniform(2, 5), 1),
            "n_encuestados": np.random.randint(180, 450),
            "fecha_estudio": "2026-02-28",
            "fuente": "Kantar BrandZ",
        })
        rows.append({
            "institucion": inst,
            "segmento_cliente": "Empresas",
            "nps": vals["corp_nps"] + np.random.randint(-2, 3),
            "satisfaccion_pct": round(vals["corp_sat"] + np.random.uniform(-1, 1), 1),
            "recomendaria_pct": round(vals["corp_sat"] + np.random.uniform(2, 5), 1),
            "n_encuestados": np.random.randint(80, 200),
            "fecha_estudio": "2026-02-28",
            "fuente": "Kantar BrandZ",
        })

    df = pd.DataFrame(rows)

    # --- Issue 1: NPS out of valid range ---
    mask = (df["institucion"] == "BHD León") & (df["segmento_cliente"] == "Empresas")
    df.loc[mask, "nps"] = 155

    # --- Issue 2: satisfaccion_pct > 100 ---
    mask = (df["institucion"] == "Banco Popular") & (df["segmento_cliente"] == "Retail")
    df.loc[mask, "satisfaccion_pct"] = 102.3

    # --- Issue 3: Duplicate row ---
    df = pd.concat([df, df[
        (df["institucion"] == "BanReservas") & (df["segmento_cliente"] == "Retail")
    ]], ignore_index=True)

    return df


def generate_nielsen_penetration(seed: int = 42) -> pd.DataFrame:
    """
    Nielsen Financial RD — Product Penetration & Rate Study (Q1 2026).

    Intentional data quality issues introduced:
      1. fecha_corte in wrong format 'DD/MM/YYYY' instead of 'YYYY-MM-DD' (fails regex contract)
      2. Null institucion for Alaver/deposito_plazo (fails not-null contract)
      3. tasa_promedio_reportada = 152.0 for Scotiabank/prestamo_personal
         (agency typo: meant 15.2% — fails 0–60 range contract)
    """
    np.random.seed(seed)

    base_rates = {
        "cuenta_ahorro": (4.0, 5.5),
        "prestamo_personal": (18.0, 24.0),
        "prestamo_hipotecario": (10.0, 14.0),
        "tarjeta_credito": (30.0, 42.0),
        "deposito_plazo": (6.5, 9.5),
    }

    rows = []
    for inst in VALID_INSTITUTIONS:
        for prod in PRODUCTS:
            lo, hi = base_rates[prod]
            rows.append({
                "institucion": inst,
                "producto": prod,
                "penetracion_pct": round(np.random.uniform(8, 42), 1),
                "tasa_promedio_reportada": round(np.random.uniform(lo, hi), 2),
                "fecha_corte": "31/03/2026",   # wrong format (intentional)
                "fuente": "Nielsen Financial RD",
            })

    df = pd.DataFrame(rows)

    # --- Issue 2: Null institution ---
    mask = (df["institucion"] == "Alaver") & (df["producto"] == "deposito_plazo")
    df.loc[mask, "institucion"] = None

    # --- Issue 3: Rate typo (152 instead of 15.2) ---
    mask = (df["institucion"] == "Scotiabank RD") & (df["producto"] == "prestamo_personal")
    df.loc[mask, "tasa_promedio_reportada"] = 152.0

    return df


def save_agency_reports() -> dict:
    """Save all 3 agency reports to data/agency/. Returns dict of {name: Path}."""
    AGENCY_DIR.mkdir(parents=True, exist_ok=True)

    reports = {
        "ipsos_market_share":  generate_ipsos_market_share(),
        "kantar_satisfaction": generate_kantar_satisfaction(),
        "nielsen_penetration": generate_nielsen_penetration(),
    }

    paths = {}
    for name, df in reports.items():
        path = AGENCY_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        paths[name] = path
        print(f"  [agency] {name}.csv  — {len(df)} rows, {df.shape[1]} columns")

    return paths


if __name__ == "__main__":
    paths = save_agency_reports()
    print(f"\nSaved to: {AGENCY_DIR}")
