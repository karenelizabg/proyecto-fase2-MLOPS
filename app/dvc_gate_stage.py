"""DVC stage that blocks downstream stages when the report is failed."""

import logging
import os
from pathlib import Path

from presentation.contracts import QualityReport

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", REPO_ROOT / "reports"))
REPORT_PATH = REPORTS_DIR / "quality.json"
PASS_MARKER = REPORTS_DIR / ".quality_gate.passed"
logger = logging.getLogger("dvc-quality-gate")


def enforce_quality_gate() -> int:
    """Return a non-zero status for failed reports and mark accepted reports."""
    PASS_MARKER.unlink(missing_ok=True)
    if not REPORT_PATH.exists():
        logger.error("No existe el reporte de calidad: %s", REPORT_PATH)
        return 1

    try:
        report = QualityReport.model_validate_json(REPORT_PATH.read_text(encoding="utf-8"))
    except ValueError:
        logger.exception("El reporte de calidad no cumple el contrato: %s", REPORT_PATH)
        return 1

    if report.status == "failed":
        logger.error("Compuerta de calidad BLOQUEADA: el reporte tiene status=failed.")
        return 1

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PASS_MARKER.write_text("passed\n", encoding="utf-8")
    logger.info("Compuerta de calidad OK (status=%s).", report.status)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(enforce_quality_gate())
