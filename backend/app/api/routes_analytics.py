"""
Endpoints analytics.
Privados (montados en :8001):
  - POST /internal/db/create_analytics_tables -> crea las 4 tablas en RDS
  - POST /internal/db/load_analytics_to_rds   -> carga Parquets de S3 a RDS

Públicos de lectura (montados en :8000, para dashboards del frontend):
  - GET  /analytics/indicadores       -> lista de indicadores
  - GET  /analytics/serie_trimestral  -> serie trimestral por indicador
  - GET  /analytics/serie_anual       -> serie anual por indicador
  - GET  /analytics/kpis              -> último valor de cada indicador
"""

# Recomendacion para dashboard a implementar:
#  1. Home de analytics: tarjetas de KPI con /analytics/kpis → último valor trimestral agregado de cada indicador.
#  2. Selector de indicador: un <select> poblado con /analytics/indicadores, filtrable por tipo.
#  3. Gráfica: al seleccionar un indicador → llamada a /analytics/serie_trimestral?id_indicador=X → <LineChart> de Recharts (anio-trimestre en X, valor en Y).
#  4. Filtros de corte: dropdowns para sexo, situacion_jornada, sexo_edad_estudios que añaden query params a la llamada.

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.services.analytics_service import (
    create_analytics_tables,
    load_analytics_to_rds,
    get_indicadores,
    get_serie_trimestral,
    get_serie_anual,
    get_ultimo_valor_por_indicador,
)

logger = logging.getLogger(__name__)

# Dos routers: uno privado (admin) y otro público (lectura)
private_router = APIRouter(tags=["analytics-admin"])
public_router  = APIRouter(tags=["analytics"])


# Privados (admin): creación y carga

@private_router.post("/internal/db/create_analytics_tables")
def create_analytics_tables_endpoint():
    """Crea (si no existen) las 4 tablas analíticas en RDS. Idempotente."""
    try:
        created = create_analytics_tables()
        return {
            "status": "ok",
            "tables": created,
            "message": "Tablas analíticas creadas o ya existían.",
        }
    except Exception as e:
        raise HTTPException(500, f"Error creando tablas analíticas: {e}")


@private_router.post("/internal/db/load_analytics_to_rds")
def load_analytics_to_rds_endpoint(
    truncate: bool = Query(
        default=True,
        description="Si True, vacía las tablas antes de insertar (re-carga completa).",
    ),
):
    """Lee los 4 Parquets de s3://.../analytics/ y los carga a RDS MySQL."""
    try:
        summary = load_analytics_to_rds(truncate_before=truncate)
        total = sum(v["rows"] for v in summary.values())
        return {
            "status":     "ok",
            "truncated":  truncate,
            "total_rows": total,
            "detail":     summary,
        }
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error cargando analytics a RDS: {e}")


# Públicos (lectura para dashboards)
@public_router.get("/analytics/indicadores")
def list_indicadores(
    tipo: Optional[str] = Query(
        default=None,
        description="Filtra por tipo: absoluto_miles | porcentaje | tasa | otro",
    ),
):
    """Lista de indicadores disponibles, con sus ids y tipos."""
    try:
        rows = get_indicadores(tipo=tipo)
        return {"count": len(rows), "indicadores": rows}
    except Exception as e:
        raise HTTPException(500, f"Error consultando indicadores: {e}")


@public_router.get("/analytics/serie_trimestral")
def serie_trimestral(
    id_indicador: int = Query(..., description="ID del indicador (ver /analytics/indicadores)"),
    sexo: Optional[str]               = Query(default=None),
    situacion_jornada: Optional[str]  = Query(default=None),
    sexo_edad_estudios: Optional[str] = Query(default=None),
):
    """Serie trimestral de un indicador, con cortes demográficos opcionales."""
    try:
        rows = get_serie_trimestral(
            id_indicador=id_indicador,
            sexo=sexo,
            situacion_jornada=situacion_jornada,
            sexo_edad_estudios=sexo_edad_estudios,
        )
        return {"count": len(rows), "serie": rows}
    except Exception as e:
        raise HTTPException(500, f"Error consultando serie trimestral: {e}")


@public_router.get("/analytics/serie_anual")
def serie_anual(
    id_indicador: int = Query(..., description="ID del indicador (ver /analytics/indicadores)"),
    sexo: Optional[str]               = Query(default=None),
    situacion_jornada: Optional[str]  = Query(default=None),
    sexo_edad_estudios: Optional[str] = Query(default=None),
):
    """Serie de medias anuales de un indicador, con cortes demográficos opcionales."""
    try:
        rows = get_serie_anual(
            id_indicador=id_indicador,
            sexo=sexo,
            situacion_jornada=situacion_jornada,
            sexo_edad_estudios=sexo_edad_estudios,
        )
        return {"count": len(rows), "serie": rows}
    except Exception as e:
        raise HTTPException(500, f"Error consultando serie anual: {e}")


@public_router.get("/analytics/kpis")
def kpis():
    """Último valor trimestral agregado (sin cortes) por cada indicador.
    Ideal para tarjetas de KPIs en la home del dashboard.
    """
    try:
        rows = get_ultimo_valor_por_indicador()
        return {"count": len(rows), "kpis": rows}
    except Exception as e:
        raise HTTPException(500, f"Error consultando KPIs: {e}")