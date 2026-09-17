"""Tier 1 — combina los lotes reales de anotaciones en un solo CocoDataset.

Cada `annotations-lote-*.json` en `data/raw/annotations/` es autocontenido
(ver app/ingestion/README.md); este módulo es el único punto donde se
juntan antes de validarse como un solo documento. Si dos lotes reintroducen
el bug de [[project_dataset_id_collision_bug]] (ids repetidos entre
archivos), `CocoDataset.model_validate` lo rechaza aquí, no río abajo.
"""

import json
from pathlib import Path

from ingestion.models import CocoDataset


def load_dataset(annotations_dir: Path) -> CocoDataset:
    """Lee y valida todos los `*.json` de `annotations_dir` como un solo dataset.

    Las categorías se deduplican por id (el seeder del portal siempre asigna
    los mismos ids fijos: person=1, car=2, dog=3, cat=4), quedándose con la
    primera aparición.
    """
    files = sorted(annotations_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No se encontraron lotes de anotaciones en {annotations_dir}")

    images = []
    annotations = []
    categories_by_id: dict[int, dict] = {}
    for path in files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        images.extend(raw["images"])
        annotations.extend(raw["annotations"])
        for category in raw["categories"]:
            categories_by_id.setdefault(category["id"], category)

    return CocoDataset.model_validate(
        {
            "images": images,
            "annotations": annotations,
            "categories": list(categories_by_id.values()),
        }
    )
