import json
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from policies.models import load_quality_policy
from presentation.gate import build_quality_report, main, run
from storage.settings import Settings

QUALITY_YAML = """
min_images_per_class:
  threshold: {min_images}
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
    """pHash mira estructura, no color plano: un cuadro sólido no basta para
    que dos imágenes se vean distintas. Se dibuja un rectángulo en una
    posición distinta por `seed` para dar estructura real."""
    image = Image.new("RGB", (64, 64), color=(20, 20, 20))
    draw = ImageDraw.Draw(image)
    x0 = (seed * 11) % 40
    y0 = (seed * 17) % 40
    draw.rectangle([x0, y0, x0 + 20, y0 + 20], fill=(220, 220, 220))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _write_dataset(tmp_path, *, cats=2, dogs=2):
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


def _policy_path(tmp_path, min_images=2):
    path = tmp_path / "quality.yaml"
    path.write_text(QUALITY_YAML.format(min_images=min_images), encoding="utf-8")
    return path


def test_report_has_six_checks_not_seven(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset")
    policy_path = _policy_path(tmp_path)
    policy = load_quality_policy(policy_path)

    report = build_quality_report(
        dataset_dir=dataset_dir,
        policy=policy,
        dataset_version="test-1",
        policy_path=policy_path,
    )

    names = {check.check_name for check in report.checks}
    assert names == {
        "min_images_per_class",
        "max_imbalance_ratio",
        "max_small_object_ratio",
        "degenerate_boxes",
        "duplicate_similarity_threshold",
        "spatial_bias",
    }
    assert "cross_split_leakage" not in names


def test_status_passed_when_everything_meets_threshold(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset", cats=2, dogs=2)
    policy_path = _policy_path(tmp_path, min_images=2)
    policy = load_quality_policy(policy_path)

    report = build_quality_report(
        dataset_dir=dataset_dir, policy=policy, dataset_version="test-1", policy_path=policy_path
    )

    assert report.status == "passed"
    assert all(check.passed for check in report.checks)


def test_status_failed_when_a_fail_action_check_does_not_pass(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset", cats=2, dogs=2)
    # Umbral imposible: ninguna clase real tiene 99999 imágenes.
    policy_path = _policy_path(tmp_path, min_images=99999)
    policy = load_quality_policy(policy_path)

    report = build_quality_report(
        dataset_dir=dataset_dir, policy=policy, dataset_version="test-1", policy_path=policy_path
    )

    assert report.status == "failed"
    min_images_check = next(c for c in report.checks if c.check_name == "min_images_per_class")
    assert not min_images_check.passed


def test_min_images_per_class_check_reports_classes_below_minimum(tmp_path):
    dataset_dir = _write_dataset(tmp_path / "dataset", cats=1, dogs=2)
    policy_path = _policy_path(tmp_path, min_images=2)
    policy = load_quality_policy(policy_path)

    report = build_quality_report(
        dataset_dir=dataset_dir, policy=policy, dataset_version="test-1", policy_path=policy_path
    )

    min_images_check = next(c for c in report.checks if c.check_name == "min_images_per_class")
    below = min_images_check.details["classes_below_minimum"]
    assert [c["category_name"] for c in below] == ["cat"]


def test_run_writes_quality_json(tmp_path, monkeypatch):
    dataset_dir = _write_dataset(tmp_path / "dataset", cats=2, dogs=2)
    reports_dir = tmp_path / "reports"
    _policy_path(tmp_path, min_images=2)  # queda en tmp_path, no se usa: run() usa el real

    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://u:p@localhost/db")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost")
    monkeypatch.setenv("MINIO_PORT", "9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "ak")
    monkeypatch.setenv("MINIO_SECRET_KEY", "sk")
    monkeypatch.setenv("MINIO_BUCKET", "bucket")
    monkeypatch.setenv("DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("REPORTS_DIR", str(reports_dir))

    report = run(Settings())

    written = json.loads((reports_dir / "quality.json").read_text(encoding="utf-8"))
    assert written["schema_version"] == "1.0"
    assert written["status"] == report.status
    assert len(written["checks"]) == 6


def test_main_returns_nonzero_exit_code_when_failed(tmp_path, monkeypatch):
    dataset_dir = _write_dataset(tmp_path / "dataset", cats=1, dogs=1)
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://u:p@localhost/db")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost")
    monkeypatch.setenv("MINIO_PORT", "9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "ak")
    monkeypatch.setenv("MINIO_SECRET_KEY", "sk")
    monkeypatch.setenv("MINIO_BUCKET", "bucket")
    monkeypatch.setenv("DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    # El quality.yaml real (min_images_per_class=300) siempre falla contra
    # un dataset sintético de 1-2 imágenes: exit code 1 garantizado.

    assert main() == 1


@pytest.mark.parametrize("bad_field", ["min_images_per_class", "max_imbalance_ratio"])
def test_broken_policy_is_rejected_by_pydantic_not_a_key_error(tmp_path, bad_field):
    policy_path = tmp_path / "quality.yaml"
    document = QUALITY_YAML.format(min_images=2).replace(
        f"{bad_field}:\n", f"{bad_field}:\n  extra_unexpected_key: 1\n", 1
    )
    policy_path.write_text(document, encoding="utf-8")

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        load_quality_policy(policy_path)
