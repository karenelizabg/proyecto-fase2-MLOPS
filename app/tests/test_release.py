import json

import pytest

from policies.models import load_quality_policy
from presentation.release import cut_release, diff_releases
from tests._dataset_fixtures import write_coco_dataset

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


def _policy_path(tmp_path):
    path = tmp_path / "quality.yaml"
    path.write_text(QUALITY_YAML, encoding="utf-8")
    return path


def test_cut_release_writes_quality_splits_and_catalog(tmp_path):
    dataset_dir = write_coco_dataset(tmp_path / "dataset", cats=6, dogs=6)
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
    dataset_dir = write_coco_dataset(tmp_path / "dataset", cats=6, dogs=6)
    policy = load_quality_policy(_policy_path(tmp_path))

    with pytest.raises(ValueError, match="vMAJOR.MINOR.PATCH"):
        cut_release("1.0", dataset_dir=dataset_dir, reports_dir=tmp_path / "reports", policy=policy)


def test_cut_release_rejects_duplicate_version(tmp_path):
    dataset_dir = write_coco_dataset(tmp_path / "dataset", cats=6, dogs=6)
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))
    cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)

    with pytest.raises(ValueError, match="ya existe"):
        cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)


def test_diff_releases_compares_two_cut_releases(tmp_path):
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))

    dataset_a = write_coco_dataset(tmp_path / "dataset-a", cats=6, dogs=6)
    cut_release("v0.1.0", dataset_dir=dataset_a, reports_dir=reports_dir, policy=policy)

    dataset_b = write_coco_dataset(tmp_path / "dataset-b", cats=9, dogs=6)
    cut_release("v0.2.0", dataset_dir=dataset_b, reports_dir=reports_dir, policy=policy)

    diff = diff_releases("v0.1.0", "v0.2.0", reports_dir=reports_dir)

    assert diff["from"] == "v0.1.0"
    assert diff["to"] == "v0.2.0"
    assert diff["images_per_category"]["cat"] == {"from": 6, "to": 9}
    assert diff["images_per_category"]["dog"] == {"from": 6, "to": 6}


def test_diff_releases_rejects_unknown_version(tmp_path):
    reports_dir = tmp_path / "reports"
    policy = load_quality_policy(_policy_path(tmp_path))
    dataset_dir = write_coco_dataset(tmp_path / "dataset", cats=6, dogs=6)
    cut_release("v0.1.0", dataset_dir=dataset_dir, reports_dir=reports_dir, policy=policy)

    with pytest.raises(ValueError, match="no existe"):
        diff_releases("v0.1.0", "v9.9.9", reports_dir=reports_dir)
