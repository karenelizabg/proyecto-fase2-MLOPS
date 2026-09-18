import json
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from policies.models import load_quality_policy
from presentation.release import cut_release, diff_releases

QUALITY_YAML = """
min_images_per_class:
  threshold: 1
  action: fail
max_imbalance_ratio:
  threshold: 999
  action: warn
max_small_object_ratio:
  threshold: 0.99
  width_px: 1
  height_px: 1
  action: warn
degenerate_boxes:
  threshold: 0
  action: fail
cross_split_leakage:
  threshold: 0
  action: fail
duplicate_similarity_threshold:
  threshold: 0.999
  action: warn
min_spatial_dispersion:
  threshold: 0.0
  action: warn
"""


def _jpeg_bytes(seed):
    """Un rectángulo en posición distinta por seed: pHash necesita estructura,
    no un color plano, para distinguir imágenes (ver test_gate.py)."""
    image = Image.new("RGB", (64, 64), color=(20, 20, 20))
    draw = ImageDraw.Draw(image)
    x0 = (seed * 7) % 40
    y0 = (seed * 13) % 40
    draw.rectangle([x0, y0, x0 + 20, y0 + 20], fill=(220, 220, 220))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _write_dataset(tmp_path, *, cats=6, dogs=6):
    annotations_dir = tmp_path / "annotations"
    images_dir = tmp_path / "images"
    annotations_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)

    images, annotations = [], []
    image_id = 1
    ann_id = 1
    seed = 0
    for index in range(cats):
        file_name = f"cat.{index}.jpg"
        (images_dir / file_name).write_bytes(_jpeg_bytes(seed))
        seed += 1
        images.append({"id": image_id, "file_name": file_name, "width": 64, "height": 64})
        annotations.append(
            {
                "id": ann_id,
                "image_id": image_id,
                "category_id": 4,
                "bbox": [0, 0, 40, 40],
                "area": 1600.0,
                "iscrowd": 0,
            }
        )
        image_id += 1
        ann_id += 1
    for index in range(dogs):
        file_name = f"dog.{index}.jpg"
        (images_dir / file_name).write_bytes(_jpeg_bytes(seed))
        seed += 1
        images.append({"id": image_id, "file_name": file_name, "width": 64, "height": 64})
        annotations.append(
            {
                "id": ann_id,
                "image_id": image_id,
                "category_id": 3,
                "bbox": [0, 0, 40, 40],
                "area": 1600.0,
                "iscrowd": 0,
            }
        )
        image_id += 1
        ann_id += 1

    doc = {
        "images": images,
        "annotations": annotations,
        "categories": [{"id": 3, "name": "dog"}, {"id": 4, "name": "cat"}],
    }
    (annotations_dir / "lote.json").write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path


def _policy_path(tmp_path):
    path = tmp_path / "quality.yaml"
    path.write_text(QUALITY_YAML, encoding="utf-8")
    return path


def test_cut_release_writes_quality_splits_and_catalog(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset")
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))

    release = cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)

    assert release.dataset_version == "v0.1.0"
    quality_path = reports_dir / "releases" / "v0.1.0" / "quality.json"
    splits_path = reports_dir / "releases" / "v0.1.0" / "splits.json"
    assert quality_path.exists()
    assert splits_path.exists()

    catalog = json.loads((reports_dir / "versions.json").read_text(encoding="utf-8"))
    assert catalog["releases"] == [
        {
            "dataset_version": "v0.1.0",
            "quality_file": "releases/v0.1.0/quality.json",
            "splits_file": "releases/v0.1.0/splits.json",
        }
    ]

    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    assert quality["dataset_version"] == "v0.1.0"
    splits = json.loads(splits_path.read_text(encoding="utf-8"))
    assert splits["total_images"] == 12
    assert (
        splits["splits"]["train"]["image_count"]
        + splits["splits"]["validation"]["image_count"]
        + splits["splits"]["test"]["image_count"]
        == 12
    )


def test_cut_release_rejects_bad_version_format(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset")
    policy = load_quality_policy(_policy_path(tmp_path))

    with pytest.raises(ValueError, match="vMAJOR.MINOR.PATCH"):
        cut_release("1.0", dataset_dir=dataset_dir, reports_dir=tmp_path / "reports", policy=policy)


def test_cut_release_rejects_duplicate_version(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset")
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))
    cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)

    with pytest.raises(ValueError, match="ya existe"):
        cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)


def test_diff_releases_compares_two_cut_releases(tmp_path):
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))

    dataset_a = _write_dataset(tmp_path / "dataset-a", cats=6, dogs=6)
    cut_release("v0.1.0", dataset_dir=dataset_a, reports_dir=reports_dir, policy=policy)

    dataset_b = _write_dataset(tmp_path / "dataset-b", cats=9, dogs=6)
    cut_release("v0.2.0", dataset_dir=dataset_b, reports_dir=reports_dir, policy=policy)

    diff = diff_releases("v0.1.0", "v0.2.0", reports_dir=reports_dir)

    assert diff["from"] == "v0.1.0"
    assert diff["to"] == "v0.2.0"
    assert diff["images_per_category"]["cat"] == {"from": 6, "to": 9}
    assert diff["images_per_category"]["dog"] == {"from": 6, "to": 6}


def test_diff_releases_rejects_unknown_version(tmp_path):
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))
    dataset_dir = _write_dataset(tmp_path / "dataset")
    cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)

    with pytest.raises(ValueError, match="no existe"):
        diff_releases("v0.1.0", "v9.9.9", reports_dir=reports_dir)
