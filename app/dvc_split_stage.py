"""DVC stage that materializes the split report after the quality gate."""

import os
from pathlib import Path

from policies.models import load_quality_policy
from presentation.gate import evaluate_dataset
from presentation.splits import build_splits_report
from splits.models import load_splits_config

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(os.environ.get("DATASET_DIR", REPO_ROOT / "data" / "raw"))
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", REPO_ROOT / "reports"))
DATASET_VERSION = os.environ.get("DATASET_VERSION", "local-dev")


def write_split_report() -> None:
    """Run the shared split logic and persist its public contract."""
    policy = load_quality_policy()
    splits_config = load_splits_config()
    _, split_result = evaluate_dataset(
        dataset_dir=DATASET_DIR,
        policy=policy,
        dataset_version=DATASET_VERSION,
        splits_config=splits_config,
    )
    report = build_splits_report(split_result, dataset_version=DATASET_VERSION)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "splits.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_split_report()
