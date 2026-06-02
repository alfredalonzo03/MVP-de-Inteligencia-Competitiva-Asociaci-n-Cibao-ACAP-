"""
Competitor Data Generator — Datos sintéticos del sector financiero dominicano
Genera datos realistas (pero ficticios) de competidores de ACAP para análisis
de inteligencia competitiva.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ── Instituciones del mercado dominicano (datos representativos, no reales) ──
COMPETITORS = {
    "BanReservas": {
        "tipo": "Banco Estatal",
        "tamaño": "Grande",
        "sucursales": 180,
        "empleados": 9500,
        "activos_usd_mm": 12_500,
        "segmento_foco": ["Empresarial", "Personal", "Hipotecario"],
    },
    "Banco Popular": {
        "tipo": "Banco Comercial",
        "tamaño": "Grande",
        "sucursales": 160,
        "empleados": 8200,
        "activos_usd_mm": 11_000,
        "segmento_foco": ["Empresarial", "Personal", "Tarjeta de Crédito"],
    },
    "BHD León": {
        "tipo": "Banco Comercial",
        "tamaño": "Grande",
        "sucursales": 130,
        "empleados": 6800,
        "activos_usd_mm": 9_500,
        "segmento_foco": ["Empresarial", "Personal", "Hipotecario"],
    },
    "Scotiabank RD": {
        "tipo": "Banco Internacional",
        "tamaño": "Mediano",
        "sucursales": 55,
        "empleados": 2100,
        "activos_usd_mm": 3_200,
        "segmento_foco": ["Empresarial", "Personal"],
    },
    "Asociación Cibao (ACAP)": {
        "tipo": "Asociación de Ahorros",
        "tamaño": "Mediano",
        "sucursales": 42,
        "empleados": 1800,
        "activos_usd_mm": 2_800,
        "segmento_foco": ["Hipotecario", "Personal", "Empresarial"],
    },
    "Alaver": {
        "tipo": "Asociación de Ahorros",
        "tamaño": "Pequeño",
        "sucursales": 28,
        "empleados": 950,
        "activos_usd_mm": 1_400,
        "segmento_foco": ["Personal", "Hipotecario"],
    },
    "ADEMI": {
        "tipo": "Banco Microfinanciero",
        "tamaño": "Pequeño",
        "sucursales": 35,
        "empleados": 1100,
        "activos_usd_mm": 900,
        "segmento_foco": ["Microcrédito", "Empresarial MIPYME"],
    },
}

PRODUCTS = ["prestamo_personal", "prestamo_hipotecario", "prestamo_vehiculo",
            "prestamo_comercial", "cuenta_ahorro", "cuenta_corriente",
            "deposito_plazo", "tarjeta_credito"]


def generate_institution_profiles() -> pd.DataFrame:
    """
    Genera tabla de perfiles institucionales de competidores.
    """
    rows = []
    for inst, attrs in COMPETITORS.items():
        rows.append({
            "institucion": inst,
            "tipo": attrs["tipo"],
            "tamaño": attrs["tamaño"],
            "sucursales": attrs["sucursales"],
            "empleados": attrs["empleados"],
            "activos_usd_mm": attrs["activos_usd_mm"],
            "segmentos": ", ".join(attrs["segmento_foco"]),
            "presencia_digital": _digital_score(inst),
            "calificacion_riesgo": _risk_rating(attrs["tamaño"]),
        })
    return pd.DataFrame(rows)


def generate_product_rates(months: int = 24) -> pd.DataFrame:
    """
    Genera series de tiempo de tasas de interés por producto e institución.

    Args:
        months: Número de meses históricos a generar.

    Returns:
        DataFrame con columnas: fecha, institucion, producto, tasa_activa, tasa_pasiva.
    """
    end_date = datetime.today().replace(day=1)
    dates = [end_date - timedelta(days=30 * i) for i in range(months)]
    dates = sorted(dates)

    base_rates = {
        "prestamo_personal":    {"activa": 22.0, "pasiva": None},
        "prestamo_hipotecario": {"activa": 11.5, "pasiva": None},
        "prestamo_vehiculo":    {"activa": 15.0, "pasiva": None},
        "prestamo_comercial":   {"activa": 14.0, "pasiva": None},
        "cuenta_ahorro":        {"activa": None, "pasiva": 4.5},
        "cuenta_corriente":     {"activa": None, "pasiva": 1.5},
        "deposito_plazo":       {"activa": None, "pasiva": 8.5},
        "tarjeta_credito":      {"activa": 36.0, "pasiva": None},
    }

    # Factores de ajuste competitivo por institución
    rate_adjustments = {
        "BanReservas":             -1.5,
        "Banco Popular":           -1.0,
        "BHD León":                -0.8,
        "Scotiabank RD":           -0.5,
        "Asociación Cibao (ACAP)": +0.3,
        "Alaver":                  +1.2,
        "ADEMI":                   +4.5,
    }

    rows = []
    for inst in COMPETITORS:
        adj = rate_adjustments[inst]
        for product in PRODUCTS:
            base = base_rates[product]
            for i, date in enumerate(dates):
                # Simula tendencia leve + ruido aleatorio
                trend = i * 0.02 * (1 if inst in ["BanReservas", "Banco Popular"] else -0.5)
                noise = np.random.normal(0, 0.3)
                rows.append({
                    "fecha": date.strftime("%Y-%m-%d"),
                    "institucion": inst,
                    "producto": product,
                    "tasa_activa": round(base["activa"] + adj + trend + noise, 2)
                                   if base["activa"] else None,
                    "tasa_pasiva": round(base["pasiva"] + (adj * -0.3) + noise * 0.5, 2)
                                   if base["pasiva"] else None,
                })

    return pd.DataFrame(rows)


def generate_market_share() -> pd.DataFrame:
    """
    Genera tabla de participación de mercado por institución y segmento.
    """
    segments = ["Hipotecario", "Personal", "Comercial", "Microcrédito", "Ahorros"]
    rows = []
    for segment in segments:
        shares = _generate_shares(list(COMPETITORS.keys()), segment)
        for inst, share in shares.items():
            rows.append({
                "segmento": segment,
                "institucion": inst,
                "participacion_pct": share,
                "year": datetime.today().year,
            })
    return pd.DataFrame(rows)


def generate_customer_segments() -> pd.DataFrame:
    """
    Genera datos de segmentación de clientes (edad, ingreso, producto, NPS).
    """
    n = 5000
    ages = np.random.normal(38, 12, n).clip(18, 75).astype(int)
    incomes = np.random.lognormal(mean=10.5, sigma=0.6, size=n).astype(int)  # DOP/mes

    segments = np.select(
        [incomes < 30_000, incomes < 80_000, incomes < 200_000],
        ["Bajo", "Medio", "Medio-Alto"],
        default="Alto"
    )

    products_taken = np.random.choice(PRODUCTS, size=n, p=[0.20, 0.18, 0.10,
                                                            0.12, 0.15, 0.08,
                                                            0.10, 0.07])
    nps = np.random.normal(35, 20, n).clip(-100, 100).astype(int)
    tenure_years = np.random.exponential(scale=4, size=n).clip(0, 30).astype(int)
    digital_user = np.random.choice([True, False], size=n, p=[0.62, 0.38])

    return pd.DataFrame({
        "cliente_id": [f"CLI{str(i).zfill(5)}" for i in range(1, n + 1)],
        "edad": ages,
        "ingreso_mensual_dop": incomes,
        "segmento_ingreso": segments,
        "producto_principal": products_taken,
        "nps": nps,
        "antiguedad_años": tenure_years,
        "usuario_digital": digital_user,
    })


def generate_competitive_events() -> pd.DataFrame:
    """
    Genera log de eventos competitivos (lanzamientos, cambios de tasa, campañas).
    """
    event_types = ["Lanzamiento de producto", "Reducción de tasa", "Incremento de tasa",
                   "Apertura de sucursal", "Campaña de marketing", "Alianza estratégica",
                   "Nuevo canal digital", "Reducción de comisiones"]
    rows = []
    end_date = datetime.today()

    for inst in COMPETITORS:
        if inst == "Asociación Cibao (ACAP)":
            continue  # ACAP es nuestra institución, no la monitoreamos como externa
        num_events = random.randint(8, 20)
        for _ in range(num_events):
            days_ago = random.randint(0, 365)
            rows.append({
                "fecha": (end_date - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                "institucion": inst,
                "tipo_evento": random.choice(event_types),
                "descripcion": _generate_event_description(inst),
                "impacto_estimado": random.choice(["Alto", "Medio", "Bajo"]),
            })

    df = pd.DataFrame(rows)
    return df.sort_values("fecha", ascending=False).reset_index(drop=True)


# ── Helpers privados ──────────────────────────────────────────────────────────

def _digital_score(institution: str) -> int:
    scores = {
        "BanReservas": 72, "Banco Popular": 85, "BHD León": 88,
        "Scotiabank RD": 80, "Asociación Cibao (ACAP)": 58,
        "Alaver": 45, "ADEMI": 40,
    }
    return scores.get(institution, 50)


def _risk_rating(size: str) -> str:
    return {"Grande": "AA-", "Mediano": "A+", "Pequeño": "A-"}.get(size, "BBB")


def _generate_shares(institutions: list, segment: str) -> dict:
    """Genera participación de mercado que suma 100%."""
    weights = {
        "BanReservas": 28, "Banco Popular": 24, "BHD León": 18,
        "Scotiabank RD": 8, "Asociación Cibao (ACAP)": 10,
        "Alaver": 6, "ADEMI": 6,
    }
    # Ajustar según segmento
    if segment == "Hipotecario":
        weights["Asociación Cibao (ACAP)"] += 5
        weights["Alaver"] += 3
        weights["BanReservas"] -= 4
        weights["Banco Popular"] -= 4
    elif segment == "Microcrédito":
        weights["ADEMI"] += 15
        weights["BanReservas"] -= 8
        weights["Banco Popular"] -= 7
    elif segment == "Ahorros":
        weights["Asociación Cibao (ACAP)"] += 4
        weights["Alaver"] += 4
        weights["BHD León"] -= 4
        weights["Scotiabank RD"] -= 4

    total = sum(weights.values())
    return {k: round(v / total * 100, 1) for k, v in weights.items()}


def _generate_event_description(institution: str) -> str:
    descriptions = [
        f"{institution} lanza nueva línea de préstamos con condiciones especiales para clientes digitales.",
        f"{institution} anuncia reducción de tasas en productos hipotecarios.",
        f"{institution} expande su red de sucursales en el interior del país.",
        f"{institution} lanza aplicación móvil con funcionalidades de inversión.",
        f"{institution} anuncia alianza con fintech para servicios de pago digital.",
        f"{institution} reduce comisiones en transferencias internacionales.",
        f"{institution} lanza programa de fidelización para clientes premium.",
        f"{institution} anuncia incremento de tasas en depósitos a plazo.",
    ]
    return random.choice(descriptions)


if __name__ == "__main__":
    print("=== Generando datos sintéticos ===\n")

    profiles = generate_institution_profiles()
    print(f"Perfiles institucionales: {len(profiles)} instituciones")
    print(profiles[["institucion", "tipo", "activos_usd_mm", "sucursales"]].to_string(index=False))

    rates = generate_product_rates(months=12)
    print(f"\nRegistros de tasas: {len(rates):,}")

    market = generate_market_share()
    print(f"Participación de mercado: {len(market)} registros")

    segments = generate_customer_segments()
    print(f"Segmentos de clientes: {len(segments):,} clientes sintéticos")

    events = generate_competitive_events()
    print(f"Eventos competitivos: {len(events)} eventos\n")
    print("Últimos 5 eventos:")
    print(events.head(5)[["fecha", "institucion", "tipo_evento", "impacto_estimado"]].to_string(index=False))
