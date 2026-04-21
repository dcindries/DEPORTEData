"""
Job 1: UN CSV en raw/ -> curated/ (parquet particionado).

Uso:
    spark-submit job1_curation.py <nombre_dataset>

Ejemplo:
    spark-submit job1_curation.py trimestral_jornada_laboral

Estructura de salida:
    curated/dataset=<nombre>/anio=YYYY/part-*.parquet

Los 7 datasets tienen schemas heterogéneos; este job los unifica a un schema
canónico con NULL en las columnas de dimensión que no aplican.

Resultado (tipo parquet) de salida:
    dataset              string    (PARTITION KEY)
    anio                 int       (PARTITION KEY, extraído de `periodo`)
    frecuencia           string    ("trimestral" | "anual" | "anual_mm")
    trimestre            int       (1-4, null para anuales)
    periodo_raw          string    (periodo tal como viene del CSV)
    indicador            string
    situacion_jornada    string    (null si no aplica)
    sexo_edad_estudios   string    (null si no aplica)
    sexo                 string    (null si no aplica)
    valor                double
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# Configuracion S3
BUCKET  = os.environ.get("S3_BUCKET_DATALAKE", "deportedata-datalake")
PROJECT = os.environ.get("NOM_USER_ID",        "deportedata_proyect")

BASE    = f"s3a://{BUCKET}/deportedata/{PROJECT}"
RAW     = f"{BASE}/raw"
CURATED = f"{BASE}/curated"


DATASETS = {
    "trimestral_jornada_laboral":    ("trimestral", ["situacion_jornada"]),
    "trimestral_perfil_demografico": ("trimestral", ["sexo_edad_estudios"]),
    "anual_mm_jornada":              ("anual_mm",   ["situacion_jornada"]),
    "anual_mm_perfil":               ("anual_mm",   ["sexo_edad_estudios"]),
    "medias_anuales_demografia":     ("anual",      ["sexo_edad_estudios"]),
    "medias_anuales_jornada_sexo":   ("anual",      ["situacion_jornada", "sexo"]),
    "medias_anuales_tipo_empleo":    ("anual",      ["sexo"]),
}

ALL_DIM_COLS = ["situacion_jornada", "sexo_edad_estudios", "sexo"]


def extract_anio_trimestre(frecuencia: str):
    if frecuencia == "trimestral":
        # "2025-4T"  ->  anio=2025, trimestre=4
        anio      = F.regexp_extract("periodo", r"^(\d{4})-\d+T$", 1).cast("int")
        trimestre = F.regexp_extract("periodo", r"^\d{4}-(\d+)T$", 1).cast("int")
    elif frecuencia == "anual":
        # "2025"  ->  anio=2025, trimestre=null
        anio      = F.regexp_extract("periodo", r"^(\d{4})$", 1).cast("int")
        trimestre = F.lit(None).cast("int")
    elif frecuencia == "anual_mm":
        # "De 2024-4T hasta 2025-3T"  ->  anio = año final
        anio      = F.regexp_extract("periodo", r"hasta\s+(\d{4})-\d+T$", 1).cast("int")
        trimestre = F.lit(None).cast("int")
    else:
        raise ValueError(f"Frecuencia desconocida: {frecuencia}")
    return anio, trimestre


def process_dataset(spark, name: str, frecuencia: str) -> int:
    """Lee un CSV de raw/, lo normaliza y lo escribe en curated/ particionado."""
    print(f"[job1] --- {name} (frecuencia={frecuencia}) ---")
    input_path = f"{RAW}/{name}.csv"

    df = (
        spark.read
        .option("header", True)
        .option("encoding", "UTF-8")
        .csv(input_path)
    )

    df = df.withColumn("valor", F.col("valor").cast("double"))

    # Añadir columnas
    anio_col, trimestre_col = extract_anio_trimestre(frecuencia)
    df = (
        df
        .withColumn("dataset",    F.lit(name))
        .withColumn("anio",       anio_col)
        .withColumn("trimestre",  trimestre_col)
        .withColumn("frecuencia", F.lit(frecuencia))
        .withColumnRenamed("periodo", "periodo_raw")
    )

    for col_name in ALL_DIM_COLS:
        if col_name not in df.columns:
            df = df.withColumn(col_name, F.lit(None).cast("string"))

    canonical = [
        "dataset", "anio",
        "frecuencia", "trimestre", "periodo_raw",
        "indicador",
        *ALL_DIM_COLS,
        "valor",
    ]
    df = df.select(*canonical)

    # Cache para evitar releer el CSV en los 2 counts + el write
    df.cache()

    # Descartar filas cuyo periodo no haya parseado
    total  = df.count()
    df_ok  = df.filter(F.col("anio").isNotNull())
    n_ok   = df_ok.count()
    if n_ok < total:
        print(f"[job1]   aviso: {total - n_ok} filas descartadas (periodo no parseable)")

    (df_ok
        .repartition("anio")
        .write
        .mode("overwrite")
        .partitionBy("dataset", "anio")
        .option("compression", "snappy")
        .parquet(CURATED))

    df.unpersist()

    print(f"[job1]   OK  {name}: {n_ok} filas -> {CURATED}/dataset={name}/")
    return n_ok


def main():
    # Leer dataset a procesar desde argv
    if len(sys.argv) < 2:
        print("[job1] ERROR: falta el nombre del dataset como argumento", file=sys.stderr)
        print(f"[job1] Uso: spark-submit job1_curation.py <dataset>", file=sys.stderr)
        print(f"[job1] Datasets válidos: {', '.join(sorted(DATASETS.keys()))}", file=sys.stderr)
        sys.exit(2)

    dataset_name = sys.argv[1].strip()

    if dataset_name not in DATASETS:
        print(f"[job1] ERROR: dataset '{dataset_name}' no existe", file=sys.stderr)
        print(f"[job1] Datasets válidos: {', '.join(sorted(DATASETS.keys()))}", file=sys.stderr)
        sys.exit(2)

    frecuencia, _dims = DATASETS[dataset_name]

    spark = (
        SparkSession.builder
        .appName(f"DEPORTEData_Job1_Curation_{dataset_name}")
        # Fundamental: overwrite dinámico para NO borrar particiones
        # de otros datasets al reescribir sólo éste.
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    print(f"[job1] Spark {spark.version} — master: {spark.sparkContext.master}")
    print(f"[job1] RAW     = {RAW}")
    print(f"[job1] CURATED = {CURATED}")
    print(f"[job1] DATASET = {dataset_name} (frecuencia={frecuencia})")

    try:
        n = process_dataset(spark, dataset_name, frecuencia)
        print(f"\n[job1] OK — {dataset_name}: {n} filas curadas")
    except Exception as e:
        print(f"[job1] ERROR en {dataset_name}: {e}", file=sys.stderr)
        spark.stop()
        sys.exit(1)

    spark.stop()


if __name__ == "__main__":
    main()
    