"""
BCRD Connector - Banco Central de la Republica Dominicana
Generador de indicadores economicos sinteticos calibrados con datos historicos del BCRD.

Hallazgos sobre la API del BCRD (investigacion mayo 2026)
---------------------------------------------------------

Opcion 1 - API REST  (apibcrd.bancentral.gov.do)
  URL   : https://apibcrd.bancentral.gov.do/
  Estado: REQUIERE REGISTRO institucional. No es acceso publico sin credenciales.
  Produccion: registrarse, obtener JWT y pasar Authorization: Bearer <token>
              en cada request al endpoint GET /api/serie?codigoVariable=X&desde=...

Opcion 2 - CDN Excel (cdn.bancentral.gov.do)
  URL base: https://cdn.bancentral.gov.do/documents/estadisticas/
  Estado  : Archivos descargables sin auth, pero estructura de columnas
            cambia entre versiones del Excel. No hay SLA ni contrato de API.
  Ejemplos:
    .../mercado-cambiario/documents/tipo_de_cambio_de_referencia_del_mercado.xlsx
    .../precios/documents/variacion_ipc.xlsx
    .../sector-monetario-financiero/documents/tasas_de_interes.xlsx

Decision de diseno (MVP)
  Se usan datos sinteticos calibrados con valores historicos BCRD 2023-2026.
  En produccion: reemplazar generate_indicators() con llamadas al REST API
  autenticado del BCRD una vez completado el registro institucional.

Referencias
  Mercado cambiario : https://www.bancentral.gov.do/a/d/2538-mercado-cambiario
  Precios / IPC     : https://www.bancentral.gov.do/a/d/2534-precios
  Sector monetario  : https://www.bancentral.gov.do/a/d/2536-sector-monetario-y-financiero
  Portal API        : https://apibcrd.bancentral.gov.do/
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Valores base calibrados con publicaciones del BCRD (promedio 2024-2026)
BASE_VALUES = {
    "tasa_referencia":    7.00,    # Tasa politica monetaria (%)
    "tasa_prestamos":    15.50,    # Tasa activa promedio (%)
    "tasa_depositos":     7.20,    # Tasa pasiva promedio (%)
    "tipo_cambio_compra": 58.50,   # DOP / USD compra
    "tipo_cambio_venta":  59.10,   # DOP / USD venta
    "inflacion":           4.80,   # Variacion mensual IPC (%)
    "reservas_internac": 14500,    # Reservas brutas (millones USD)
}

VOLATILITY = {
    "tasa_referencia":    0.15,
    "tasa_prestamos":     0.20,
    "tasa_depositos":     0.18,
    "tipo_cambio_compra": 0.25,
    "tipo_cambio_venta":  0.25,
    "inflacion":          0.30,
    "reservas_internac": 150.0,
}


def generate_indicators(months: int = 24) -> pd.DataFrame:
    """
    Genera series de tiempo de indicadores economicos sinteticos.
    Calibrados con datos historicos del BCRD 2023-2026.

    Args:
        months: Numero de meses de historia a generar.

    Returns:
        DataFrame indexado por fecha (frecuencia mensual).
        .attrs["fuente"] describe el origen de los datos.
    """
    np.random.seed(42)
    end_date = datetime.today().replace(day=1)
    dates = pd.date_range(end=end_date, periods=months, freq="MS")

    data = {}
    for indicator, start_val in BASE_VALUES.items():
        noise = np.random.normal(0, VOLATILITY[indicator], months)
        # Tipo de cambio tiene tendencia leve al alza (~2% anual)
        trend = np.linspace(0, 0.02 * start_val, months) if "cambio" in indicator else 0
        series = start_val + np.cumsum(noise) * 0.3 + trend
        series = np.clip(series, start_val * 0.70, start_val * 1.40)
        data[indicator] = np.round(series, 4)

    df = pd.DataFrame(data, index=dates)
    df.index.name = "fecha"
    df.attrs["fuente"] = "Sintetico calibrado BCRD 2024-2026"
    logger.info("Indicadores generados: %d periodos, %d variables", len(df), len(df.columns))
    return df


def get_latest_rates() -> dict:
    """Retorna el valor mas reciente de cada indicador."""
    df = generate_indicators()
    fuente = df.attrs.get("fuente", "Desconocido")
    result = {}
    for col in df.columns:
        series = df[col].dropna()
        if not series.empty:
            result[col] = {
                "valor": round(float(series.iloc[-1]), 4),
                "fecha": series.index[-1].strftime("%Y-%m-%d"),
                "fuente": fuente,
            }
    return result


if __name__ == "__main__":
    print("=== Indicadores Economicos BCRD (datos sinteticos) ===\n")
    rates = get_latest_rates()
    print(f"  {'Indicador':<25}  {'Valor':>10}  {'Fecha':<12}  Fuente")
    print("  " + "-" * 65)
    for name, info in rates.items():
        print(f"  {name:<25}  {info['valor']:>10}  {info['fecha']}  {info['fuente']}")
