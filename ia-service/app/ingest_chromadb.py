"""
  Formato:
  {
      "ids":       ["dirce_deportes_2024_001", ...],
      "documents": ["Texto del chunk...", ...],
      "metadatas": [{"fuente": "DIRCE", "tema": "...", "año": 2024}, ...]
  }
Uso dentro del contenedor (una sola vez o tras cambiar los JSON):
    docker exec -it deportedata-ia python -m app.ingest_chromadb
"""

from __future__ import annotations

import glob
import json
import logging
import os
import sys
from typing import Iterable, List, Tuple

import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _sanitize_metadata(meta: dict, default_fuente: str) -> dict:
    """Garantiza tipos válidos para Chroma (str/int/float/bool) y rellena 'fuente'."""
    if not isinstance(meta, dict):
        meta = {}
    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            # Listas, dicts u otros → JSON-stringify para no perder info
            out[k] = json.dumps(v, ensure_ascii=False)
    if not out.get("fuente"):
        out["fuente"] = default_fuente
    return out


def _iter_chunks_legacy(data: dict, default_fuente: str) -> Iterable[Tuple[str, str, dict]]:
    """Formato A: {chunks: [{chunk_id, texto, fuente}, ...]}"""
    for chunk in data.get("chunks", []):
        cid = chunk.get("chunk_id")
        texto = chunk.get("texto")
        if not cid or not texto:
            continue
        meta = {"fuente": chunk.get("fuente") or default_fuente}
        yield cid, texto, meta


def _iter_chunks_native(data: dict, default_fuente: str) -> Iterable[Tuple[str, str, dict]]:
    """Formato B: {ids: [...], documents: [...], metadatas: [...]}"""
    ids = data.get("ids", []) or []
    docs = data.get("documents", []) or []
    metas = data.get("metadatas", []) or []

    if len(ids) != len(docs):
        logger.warning(
            "Longitudes inconsistentes ids=%s documents=%s en fichero — se ignora",
            len(ids), len(docs),
        )
        return

    # metadatas puede venir más corta o vacía → rellenamos con dicts vacíos
    if len(metas) < len(ids):
        metas = list(metas) + [{}] * (len(ids) - len(metas))

    for cid, texto, meta in zip(ids, docs, metas):
        if not cid or not texto:
            continue
        yield str(cid), str(texto), _sanitize_metadata(meta, default_fuente)


def _iter_file(path: str) -> Iterable[Tuple[str, str, dict]]:
    """Carga un fichero, autodetecta el formato y emite (id, texto, meta)."""
    fname = os.path.basename(path)

    # Detectar y rechazar ficheros vacíos sin abortar la ingesta entera
    if os.path.getsize(path) == 0:
        logger.warning("Fichero vacío, se ignora: %s", fname)
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.error("No se pudo leer %s: %s", fname, exc)
        return

    if not isinstance(data, dict):
        logger.warning("Estructura inesperada (no es objeto JSON): %s", fname)
        return

    default_fuente = data.get("archivo_origen") or fname

    # Autodetección: priorizamos el formato nativo si están las 3 claves
    if "ids" in data and "documents" in data:
        n_before = 0
        for triple in _iter_chunks_native(data, default_fuente):
            n_before += 1
            yield triple
        logger.info("  %s -> formato native, %s docs", fname, n_before)
    elif "chunks" in data:
        n_before = 0
        for triple in _iter_chunks_legacy(data, default_fuente):
            n_before += 1
            yield triple
        logger.info("  %s -> formato legacy, %s docs", fname, n_before)
    else:
        logger.warning(
            "  %s -> esquema desconocido (sin 'chunks' ni 'ids'/'documents'), se ignora",
            fname,
        )


def main() -> int:
    settings = get_settings()
    data_dir = settings.data_json_dir

    if not os.path.isdir(data_dir):
        logger.error("No existe el directorio %s", data_dir)
        return 1

    # Glob NO recursivo por diseño: los JSON deben estar planos en data_json/.
    json_paths = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not json_paths:
        logger.error("No hay JSON en %s", data_dir)
        return 1

    logger.info("Encontrados %s JSON en %s", len(json_paths), data_dir)

    client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # Recreamos la colección desde cero para una ingesta limpia
    try:
        client.delete_collection(settings.chroma_collection)
        logger.info("Colección previa eliminada: %s", settings.chroma_collection)
    except Exception:
        pass

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    coll = client.create_collection(
        name=settings.chroma_collection,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Batcheamos por rendimiento (200 docs por insert)
    BATCH = 200
    ids_buf: List[str] = []
    docs_buf: List[str] = []
    meta_buf: List[dict] = []
    total = 0
    seen_ids: set = set()

    def _flush():
        nonlocal total, ids_buf, docs_buf, meta_buf
        if not ids_buf:
            return
        coll.add(ids=ids_buf, documents=docs_buf, metadatas=meta_buf)
        total += len(ids_buf)
        ids_buf, docs_buf, meta_buf = [], [], []

    for path in json_paths:
        for cid, texto, meta in _iter_file(path):
            # Evitar IDs duplicados entre ficheros distintos (Chroma da error)
            if cid in seen_ids:
                logger.warning("ID duplicado ignorado: %s (en %s)", cid, os.path.basename(path))
                continue
            seen_ids.add(cid)

            ids_buf.append(cid)
            docs_buf.append(texto)
            meta_buf.append(meta)
            if len(ids_buf) >= BATCH:
                _flush()

    _flush()

    logger.info("Ingesta completada. Documentos totales en colección: %s", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
