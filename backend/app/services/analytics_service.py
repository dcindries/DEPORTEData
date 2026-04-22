"""
DEPORTEData - Servicio de datos analíticos.

Objetivo:
  1. Crear las 4 tablas analíticas en RDS MySQL.
  2. Cargar Parquets de s3://.../analytics/ a RDS mysql db.
  3. Consultas agregadas para los dashboards del frontend.

Las 4 tablas (prefijo deportedata_*):
  - deportedata_dim_indicador   <- analytics/dim_indicador/
  - deportedata_fact_trimestral <- analytics/fact_trimestral/
  - deportedata_fact_anual      <- analytics/fact_anual/
  - deportedata_fact_anual_mm   <- analytics/fact_anual_mm/
"""

import logging
from io import BytesIO
from typing import Optional

import pandas as pd

from app.config import get_settings
from app.db.connection import get_connection, fetch_all, execute
from app.s3_client import get_s3

logger = logging.getLogger(__name__)


# Tablas (nombre lógico -> nombre físico en RDS)
TABLES = {
    "dim_indicador":   "deportedata_dim_indicador",
    "fact_trimestral": "deportedata_fact_trimestral",
    "fact_anual":      "deportedata_fact_anual",
    "fact_anual_mm":   "deportedata_fact_anual_mm",
}

# Columnas destino en MySQL, por tabla.
COLUMNS = {
    "dim_indicador":   ["id_indicador", "indicador", "tipo_indicador"],
    "fact_trimestral": ["id_indicador", "dataset", "anio", "trimestre", "periodo",
                        "situacion_jornada", "sexo_edad_estudios", "sexo", "valor"],
    "fact_anual":      ["id_indicador", "dataset", "anio", "periodo",
                        "situacion_jornada", "sexo_edad_estudios", "sexo", "valor"],
    "fact_anual_mm":   ["id_indicador", "dataset", "anio", "periodo",
                        "situacion_jornada", "sexo_edad_estudios", "sexo", "valor"],
}


# DDL
CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS `deportedata_dim_indicador` (
        `id_indicador`   INT          NOT NULL,
        `indicador`      VARCHAR(500) NOT NULL,
        `tipo_indicador` VARCHAR(50)  NOT NULL,
        PRIMARY KEY (`id_indicador`),
        INDEX `idx_tipo` (`tipo_indicador`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `deportedata_fact_trimestral` (
        `id`                 BIGINT        NOT NULL AUTO_INCREMENT,
        `id_indicador`       INT           NULL,
        `dataset`            VARCHAR(80)   NOT NULL,
        `anio`               SMALLINT      NOT NULL,
        `trimestre`          TINYINT       NOT NULL,
        `periodo`            VARCHAR(20)   NOT NULL,
        `situacion_jornada`  VARCHAR(100)  NULL,
        `sexo_edad_estudios` VARCHAR(100)  NULL,
        `sexo`               VARCHAR(50)   NULL,
        `valor`              DECIMAL(12,3) NULL,
        PRIMARY KEY (`id`),
        INDEX `idx_indicador_anio`  (`id_indicador`, `anio`),
        INDEX `idx_dataset_periodo` (`dataset`, `anio`, `trimestre`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `deportedata_fact_anual` (
        `id`                 BIGINT        NOT NULL AUTO_INCREMENT,
        `id_indicador`       INT           NULL,
        `dataset`            VARCHAR(80)   NOT NULL,
        `anio`               SMALLINT      NOT NULL,
        `periodo`            VARCHAR(20)   NOT NULL,
        `situacion_jornada`  VARCHAR(100)  NULL,
        `sexo_edad_estudios` VARCHAR(100)  NULL,
        `sexo`               VARCHAR(50)   NULL,
        `valor`              DECIMAL(12,3) NULL,
        PRIMARY KEY (`id`),
        INDEX `idx_indicador_anio` (`id_indicador`, `anio`),
        INDEX `idx_dataset_anio`   (`dataset`, `anio`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS `deportedata_fact_anual_mm` (
        `id`                 BIGINT        NOT NULL AUTO_INCREMENT,
        `id_indicador`       INT           NULL,
        `dataset`            VARCHAR(80)   NOT NULL,
        `anio`               SMALLINT      NOT NULL,
        `periodo`            VARCHAR(80)   NOT NULL,
        `situacion_jornada`  VARCHAR(100)  NULL,
        `sexo_edad_estudios` VARCHAR(100)  NULL,
        `sexo`               VARCHAR(50)   NULL,
        `valor`              DECIMAL(12,3) NULL,
        PRIMARY KEY (`id`),
        INDEX `idx_indicador_anio` (`id_indicador`, `anio`),
        INDEX `idx_dataset_anio`   (`dataset`, `anio`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


def create_analytics_tables() -> list[str]:
    """Crea las 4 tablas si no existen. Idempotente."""
    created = []
    for ddl in CREATE_TABLES_SQL:
        execute(ddl)
        # Extraer el nombre de la tabla del DDL para el response
        name = ddl.split("`")[1]
        created.append(name)
    return created


# CARGA S3 -> MySQL
def _read_parquet_from_s3(prefix_rel: str) -> pd.DataFrame:
    """Lee todos los part-*.parquet bajo analytics/<prefix_rel>/ y los concatena.

    prefix_rel: 'dim_indicador', 'fact_trimestral', 'fact_anual', 'fact_anual_mm'
    """
    s = get_settings()
    s3 = get_s3()
    full_prefix = f"{s.s3_prefix}/analytics/{prefix_rel}/"

    # Listar los parquet bajo el prefijo (Spark genera part-*.parquet + _SUCCESS)
    paginator = s3.get_paginator("list_objects_v2")
    parquet_keys = []
    for page in paginator.paginate(Bucket=s.s3_bucket_datalake, Prefix=full_prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                parquet_keys.append(obj["Key"])

    if not parquet_keys:
        raise FileNotFoundError(
            f"No se encontraron parquets en s3://{s.s3_bucket_datalake}/{full_prefix}"
        )

    # Descargar y leer cada parquet; concatenar en un único DataFrame
    frames = []
    for key in parquet_keys:
        obj = s3.get_object(Bucket=s.s3_bucket_datalake, Key=key)
        frames.append(pd.read_parquet(BytesIO(obj["Body"].read())))
    df = pd.concat(frames, ignore_index=True)
    logger.info(f"Leído {prefix_rel}: {len(df)} filas desde {len(parquet_keys)} parquet(s)")
    return df


def _bulk_insert(table_physical: str, columns: list[str], rows: list[tuple]) -> int:
    """Inserta `rows` en `table_physical` con executemany. Devuelve nº insertadas."""
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(columns))
    col_list     = ", ".join(f"`{c}`" for c in columns)
    sql = f"INSERT INTO `{table_physical}` ({col_list}) VALUES ({placeholders})"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()
        n = cur.rowcount
        cur.close()
        return n
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _truncate(table_physical: str) -> None:
    execute(f"TRUNCATE TABLE `{table_physical}`")


def load_analytics_to_rds(truncate_before: bool = True) -> dict:
    """Lee los 4 Parquets de analytics/ y los vuelca a las tablas en RDS.

    truncate_before: si True (por defecto) vacía cada tabla antes de insertar
                     para garantizar idempotencia (re-carga completa).
    """
    # Asegurar que las tablas existen
    create_analytics_tables()

    summary = {}

    for logical_name, table_physical in TABLES.items():
        df = _read_parquet_from_s3(logical_name)
        cols = COLUMNS[logical_name]

        # Reordenar columnas según el INSERT y convertir NaN -> None
        df = df[cols].astype(object).where(pd.notnull(df[cols]), None)

        rows = list(df.itertuples(index=False, name=None))

        if truncate_before:
            _truncate(table_physical)

        n = _bulk_insert(table_physical, cols, rows)
        summary[logical_name] = {
            "table":  table_physical,
            "rows":   n,
            "source": f"analytics/{logical_name}/",
        }

    return summary


# CONSULTAS PARA DASHBOARDS
def get_indicadores(tipo: Optional[str] = None) -> list[dict]:
    """Lista de indicadores, opcionalmente filtrada por tipo."""
    if tipo:
        return fetch_all(
            "SELECT id_indicador, indicador, tipo_indicador "
            "FROM `deportedata_dim_indicador` "
            "WHERE tipo_indicador = %s "
            "ORDER BY indicador",
            (tipo,),
        )
    return fetch_all(
        "SELECT id_indicador, indicador, tipo_indicador "
        "FROM `deportedata_dim_indicador` "
        "ORDER BY indicador"
    )


def get_serie_trimestral(
    id_indicador: int,
    sexo: Optional[str] = None,
    situacion_jornada: Optional[str] = None,
    sexo_edad_estudios: Optional[str] = None,
) -> list[dict]:
    """Serie trimestral de un indicador para pintar una gráfica de líneas.

    Los filtros opcionales permiten fijar un corte demográfico concreto.
    """
    sql = [
        "SELECT anio, trimestre, periodo,",
        "       situacion_jornada, sexo_edad_estudios, sexo, valor",
        "FROM `deportedata_fact_trimestral`",
        "WHERE id_indicador = %s",
    ]
    params: list = [id_indicador]

    if sexo is not None:
        sql.append("AND sexo = %s");               params.append(sexo)
    if situacion_jornada is not None:
        sql.append("AND situacion_jornada = %s");  params.append(situacion_jornada)
    if sexo_edad_estudios is not None:
        sql.append("AND sexo_edad_estudios = %s"); params.append(sexo_edad_estudios)

    sql.append("ORDER BY anio, trimestre")
    return fetch_all(" ".join(sql), tuple(params))


def get_serie_anual(
    id_indicador: int,
    sexo: Optional[str] = None,
    situacion_jornada: Optional[str] = None,
    sexo_edad_estudios: Optional[str] = None,
) -> list[dict]:
    """Serie de medias anuales."""
    sql = [
        "SELECT anio, periodo,",
        "       situacion_jornada, sexo_edad_estudios, sexo, valor",
        "FROM `deportedata_fact_anual`",
        "WHERE id_indicador = %s",
    ]
    params: list = [id_indicador]

    if sexo is not None:
        sql.append("AND sexo = %s");               params.append(sexo)
    if situacion_jornada is not None:
        sql.append("AND situacion_jornada = %s");  params.append(situacion_jornada)
    if sexo_edad_estudios is not None:
        sql.append("AND sexo_edad_estudios = %s"); params.append(sexo_edad_estudios)

    sql.append("ORDER BY anio")
    return fetch_all(" ".join(sql), tuple(params))


def get_ultimo_valor_por_indicador() -> list[dict]:
    """KPIs para la home del dashboard: último valor de cada indicador
    en la serie trimestral, restringido al total agregado (sin cortes)."""
    sql = """
        SELECT d.id_indicador,
               d.indicador,
               d.tipo_indicador,
               t.anio,
               t.trimestre,
               t.periodo,
               t.valor
        FROM `deportedata_dim_indicador` d
        JOIN (
            SELECT t1.id_indicador, t1.anio, t1.trimestre, t1.periodo, t1.valor
            FROM `deportedata_fact_trimestral` t1
            INNER JOIN (
                SELECT id_indicador,
                       MAX(anio * 10 + trimestre) AS max_periodo
                FROM `deportedata_fact_trimestral`
                WHERE (situacion_jornada = 'TOTAL' OR situacion_jornada IS NULL)
                  AND (sexo_edad_estudios = 'TOTAL' OR sexo_edad_estudios IS NULL)
                  AND (sexo = 'Total' OR sexo IS NULL)
                GROUP BY id_indicador
            ) t2 ON t1.id_indicador = t2.id_indicador
                AND (t1.anio * 10 + t1.trimestre) = t2.max_periodo
            WHERE (t1.situacion_jornada = 'TOTAL' OR t1.situacion_jornada IS NULL)
              AND (t1.sexo_edad_estudios = 'TOTAL' OR t1.sexo_edad_estudios IS NULL)
              AND (t1.sexo = 'Total' OR t1.sexo IS NULL)
        ) t ON d.id_indicador = t.id_indicador
        ORDER BY d.indicador
    """
    return fetch_all(sql)