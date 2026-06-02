"""
Customer Segmentation — K-Means clustering de clientes de ACAP
Identifica segmentos conductuales para targeting de productos.
"""

import sqlite3
import logging
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "processed" / "competitive_intelligence.db"
CSV_DIR = ROOT / "data" / "processed"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Feature Engineering ───────────────────────────────────────────────────────

def _prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Prepara las features numéricas para clustering.

    Returns:
        (DataFrame de features escaladas, lista de nombres de features)
    """
    features = ["edad", "ingreso_mensual_dop", "nps", "antiguedad_años", "usuario_digital"]

    df_feat = df[features].copy()
    df_feat["usuario_digital"] = df_feat["usuario_digital"].astype(int)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df_feat)

    return pd.DataFrame(scaled, columns=features), features


# ── Optimal K Selection ───────────────────────────────────────────────────────

def find_optimal_k(max_k: int = 7, sample_size: int = 2000) -> pd.DataFrame:
    """
    Evalúa distintos valores de K usando Elbow (inertia) y Silhouette Score.

    Args:
        max_k: K máximo a evaluar.
        sample_size: Muestra de clientes para acelerar el cálculo.

    Returns:
        DataFrame con [k, inertia, silhouette_score].
    """
    conn = _get_conn()
    df = pd.read_sql_query("SELECT * FROM customer_segments", conn)
    conn.close()

    df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)
    X, _ = _prepare_features(df_sample)

    results = []
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        sil = silhouette_score(X, labels)
        results.append({
            "k": k,
            "inertia": round(km.inertia_, 2),
            "silhouette_score": round(sil, 4),
        })
        logger.info("  K=%d | Inertia=%.1f | Silhouette=%.4f", k, km.inertia_, sil)

    return pd.DataFrame(results)


# ── Clustering ────────────────────────────────────────────────────────────────

def run_clustering(n_clusters: int = 4) -> pd.DataFrame:
    """
    Ejecuta K-Means con el número de clusters especificado y
    enriquece el dataset de clientes con la etiqueta de segmento.

    Args:
        n_clusters: Número de clusters a generar.

    Returns:
        DataFrame de clientes con columna 'cluster' agregada.
    """
    conn = _get_conn()
    df = pd.read_sql_query("SELECT * FROM customer_segments", conn)
    conn.close()

    X, features = _prepare_features(df)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X)

    logger.info("Clustering completado: %d clientes en %d clusters", len(df), n_clusters)
    return df


# ── Cluster Profiling ─────────────────────────────────────────────────────────

def profile_clusters(df_clustered: pd.DataFrame) -> pd.DataFrame:
    """
    Genera el perfil promedio de cada cluster para interpretación estratégica.

    Args:
        df_clustered: DataFrame con columna 'cluster'.

    Returns:
        DataFrame con perfil promedio por cluster, incluyendo etiqueta interpretativa.
    """
    profile = (
        df_clustered.groupby("cluster")
        .agg(
            total_clientes=("cliente_id", "count"),
            edad_promedio=("edad", "mean"),
            ingreso_promedio_dop=("ingreso_mensual_dop", "mean"),
            nps_promedio=("nps", "mean"),
            antiguedad_promedio=("antiguedad_años", "mean"),
            pct_digital=("usuario_digital", lambda x: round(x.astype(int).mean() * 100, 1)),
        )
        .reset_index()
    )

    # Redondear
    for col in ["edad_promedio", "ingreso_promedio_dop", "nps_promedio", "antiguedad_promedio"]:
        profile[col] = profile[col].round(1)

    # Calcular % del total
    profile["pct_del_total"] = (
        profile["total_clientes"] / profile["total_clientes"].sum() * 100
    ).round(1)

    # Etiqueta interpretativa basada en ingreso y NPS
    def _label(row: pd.Series) -> str:
        if row["ingreso_promedio_dop"] > 150_000 and row["nps_promedio"] > 40:
            return "Clientes VIP — Alto valor, alta fidelidad"
        elif row["ingreso_promedio_dop"] > 80_000:
            return "Clientes Premium — Potencial de cross-sell"
        elif row["pct_digital"] > 70:
            return "Clientes Digitales — Bajo ingreso, alta adopción digital"
        else:
            return "Clientes Base — Tradicionales, bajo engagement"

    profile["etiqueta"] = profile.apply(_label, axis=1)

    return profile.sort_values("ingreso_promedio_dop", ascending=False)


# ── Product Affinity ──────────────────────────────────────────────────────────

def product_affinity_by_cluster(df_clustered: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula qué productos son más populares en cada cluster
    para guiar estrategias de cross-selling.

    Returns:
        DataFrame con distribución de productos por cluster.
    """
    affinity = (
        df_clustered.groupby(["cluster", "producto_principal"])
        .size()
        .reset_index(name="count")
    )
    total_per_cluster = df_clustered.groupby("cluster").size().reset_index(name="total")
    affinity = affinity.merge(total_per_cluster, on="cluster")
    affinity["pct"] = (affinity["count"] / affinity["total"] * 100).round(1)

    # Top producto por cluster
    top = (
        affinity.sort_values("pct", ascending=False)
        .groupby("cluster")
        .head(3)
        .sort_values(["cluster", "pct"], ascending=[True, False])
    )
    return top[["cluster", "producto_principal", "count", "pct"]]


# ── Export ────────────────────────────────────────────────────────────────────

def export_segmentation_csv(df_clustered: pd.DataFrame,
                             profile: pd.DataFrame) -> None:
    """Exporta resultados de segmentación para Power BI."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    # Solo exportar resumen (no los 5,000 clientes completos)
    profile_path = CSV_DIR / "segmentation_clusters.csv"
    profile.to_csv(profile_path, index=False, encoding="utf-8-sig")
    logger.info("Exportado: %s", profile_path.name)

    affinity = product_affinity_by_cluster(df_clustered)
    affinity_path = CSV_DIR / "segmentation_product_affinity.csv"
    affinity.to_csv(affinity_path, index=False, encoding="utf-8-sig")
    logger.info("Exportado: %s", affinity_path.name)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("=== Evaluando K óptimo (K=2 a 6) ===")
    k_eval = find_optimal_k(max_k=6)
    print(k_eval.to_string(index=False))

    best_k = int(k_eval.loc[k_eval["silhouette_score"].idxmax(), "k"])
    print(f"\nK óptimo por Silhouette: {best_k}")

    print(f"\n=== Ejecutando clustering con K={best_k} ===")
    df_clustered = run_clustering(n_clusters=best_k)

    print("\n=== Perfil de Clusters ===")
    profile = profile_clusters(df_clustered)
    print(profile[["cluster", "total_clientes", "pct_del_total",
                   "ingreso_promedio_dop", "nps_promedio",
                   "pct_digital", "etiqueta"]].to_string(index=False))

    print("\n=== Product Affinity por Cluster (Top 3) ===")
    affinity = product_affinity_by_cluster(df_clustered)
    print(affinity.to_string(index=False))

    print("\n=== Exportando CSVs de segmentación... ===")
    export_segmentation_csv(df_clustered, profile)
    print("Listo.")
