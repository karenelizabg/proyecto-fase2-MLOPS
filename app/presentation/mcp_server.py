"""Tier 6 — servidor MCP de solo lectura para el Copilot (P2-34).

Expone herramientas de consulta sobre el dataset real y sus resultados de
calidad. Cada herramienta se anota `read_only_hint=True` (`ToolAnnotations`
del protocolo MCP) y ninguna toca MariaDB/MinIO ni escribe nada a disco —
solo lee `data/raw/annotations/` (vía `ingestion.loader`, igual que
`gate.py`) y los reportes que ya escribió `presentation/gate.py` en
`REPORTS_DIR`. Ningún handler llama a `storage/` (el único tier autorizado
a tocar red/DB — ver `app/tests/test_architecture.py`), así que no hay
manera de que uno de estos handlers dispare una escritura a la base de
datos o al almacén de objetos: la capa que sabe hacer eso ni siquiera está
importada aquí (verificado por `tests/test_mcp_server.py`, que además
grepea este archivo contra los verbos SQL de escritura prohibidos).

`splits.json`/`versions.json` no existen todavía (ningún tier los produce
aún); sus herramientas devuelven `available: false` en vez de fallar o
inventar datos — mismo principio que ya usa el frontend
(`frontend/src/pipeline/dataSource.ts`).
"""

import json
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from ingestion.loader import load_dataset
from ingestion.models import CocoDataset
from storage.settings import Settings

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _dataset_summary(dataset: CocoDataset) -> dict[str, Any]:
    """Pura: cuenta imágenes distintas por categoría (igual que analyzers/imbalance.py)."""
    images_by_category: dict[int, set[int]] = {
        category.id: set() for category in dataset.categories
    }
    for annotation in dataset.annotations:
        images_by_category[annotation.category_id].add(annotation.image_id)

    return {
        "total_images": len(dataset.images),
        "total_annotations": len(dataset.annotations),
        "images_per_category": {
            category.name: len(images_by_category[category.id]) for category in dataset.categories
        },
    }


def _read_report(reports_dir: Path, filename: str) -> dict[str, Any]:
    """Pura dado el filesystem: no escribe nada, solo intenta leer un JSON ya generado."""
    path = reports_dir / filename
    if not path.exists():
        return {"available": False, "reason": f"{filename} todavía no existe"}
    return {"available": True, "data": json.loads(path.read_text(encoding="utf-8"))}


def _find_check(quality_report: dict[str, Any], check_name: str) -> dict[str, Any] | None:
    return next(
        (check for check in quality_report["checks"] if check["check_name"] == check_name), None
    )


def build_server(settings: Settings | None = None) -> MCPServer:
    settings = settings if settings is not None else Settings()
    server = MCPServer(
        name="dataset-quality-copilot",
        instructions=(
            "Consultas de solo lectura sobre el dataset de calidad (Fase 2) y sus "
            "resultados: dataset real, reporte de calidad, splits y versiones."
        ),
    )

    @server.tool(
        name="get_dataset_summary",
        description=(
            "Resumen del dataset real: total de imágenes, total de anotaciones y "
            "conteo de imágenes distintas por categoría."
        ),
        annotations=READ_ONLY,
    )
    def get_dataset_summary() -> dict[str, Any]:
        dataset = load_dataset(settings.dataset_dir / "annotations")
        return _dataset_summary(dataset)

    @server.tool(
        name="get_quality_report",
        description=(
            "Reporte de calidad real (quality.json) generado por la compuerta: "
            "status global y cada check con su valor, umbral-acción y detalle."
        ),
        annotations=READ_ONLY,
    )
    def get_quality_report() -> dict[str, Any]:
        return _read_report(settings.reports_dir, "quality.json")

    @server.tool(
        name="get_check_result",
        description=(
            "Resultado de un check de calidad específico por nombre (p. ej. 'spatial_bias')."
        ),
        annotations=READ_ONLY,
    )
    def get_check_result(check_name: str) -> dict[str, Any]:
        report = _read_report(settings.reports_dir, "quality.json")
        if not report["available"]:
            return report
        match = _find_check(report["data"], check_name)
        if match is None:
            return {"available": False, "reason": f"no existe un check llamado '{check_name}'"}
        return {"available": True, "data": match}

    @server.tool(
        name="get_splits_report",
        description="Reporte de splits (train/validation/test) del dataset, si ya existe.",
        annotations=READ_ONLY,
    )
    def get_splits_report() -> dict[str, Any]:
        return _read_report(settings.reports_dir, "splits.json")

    @server.tool(
        name="get_versions_report",
        description="Catálogo de releases publicadas del dataset (versions.json), si ya existe.",
        annotations=READ_ONLY,
    )
    def get_versions_report() -> dict[str, Any]:
        return _read_report(settings.reports_dir, "versions.json")

    return server


def main() -> None:
    server = build_server()
    server.run()


if __name__ == "__main__":
    main()
