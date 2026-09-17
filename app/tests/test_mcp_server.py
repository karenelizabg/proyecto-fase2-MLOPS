import asyncio
import json
import re
from pathlib import Path

import pytest

from presentation.mcp_server import build_server
from storage.settings import Settings

EXPECTED_TOOLS = {
    "get_dataset_summary",
    "get_quality_report",
    "get_check_result",
    "get_splits_report",
    "get_versions_report",
}


def _settings(monkeypatch, dataset_dir: Path, reports_dir: Path) -> Settings:
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://u:p@localhost/db")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost")
    monkeypatch.setenv("MINIO_PORT", "9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "ak")
    monkeypatch.setenv("MINIO_SECRET_KEY", "sk")
    monkeypatch.setenv("MINIO_BUCKET", "bucket")
    monkeypatch.setenv("DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("REPORTS_DIR", str(reports_dir))
    return Settings()


def _write_dataset(annotations_dir: Path):
    annotations_dir.mkdir(parents=True)
    doc = {
        "images": [
            {"id": 1, "file_name": "cat.0.jpg", "width": 10, "height": 10},
            {"id": 2, "file_name": "dog.0.jpg", "width": 10, "height": 10},
            {"id": 3, "file_name": "dog.1.jpg", "width": 10, "height": 10},
        ],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 4,
                "bbox": [0, 0, 5, 5],
                "area": 25.0,
                "iscrowd": 0,
            },
            {
                "id": 2,
                "image_id": 2,
                "category_id": 3,
                "bbox": [0, 0, 5, 5],
                "area": 25.0,
                "iscrowd": 0,
            },
            {
                "id": 3,
                "image_id": 3,
                "category_id": 3,
                "bbox": [0, 0, 5, 5],
                "area": 25.0,
                "iscrowd": 0,
            },
        ],
        "categories": [{"id": 3, "name": "dog"}, {"id": 4, "name": "cat"}],
    }
    (annotations_dir / "lote.json").write_text(json.dumps(doc), encoding="utf-8")


def call(server, name, arguments=None):
    return asyncio.run(server.call_tool(name, arguments or {}))


def result_json(call_result):
    return json.loads(call_result.content[0].text)


def test_registers_exactly_the_five_expected_tools(tmp_path, monkeypatch):
    settings = _settings(monkeypatch, tmp_path / "dataset", tmp_path / "reports")
    server = build_server(settings)

    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    for tool in tools:
        assert tool.description, f"{tool.name} no tiene descripción"


def test_every_tool_is_marked_read_only(tmp_path, monkeypatch):
    settings = _settings(monkeypatch, tmp_path / "dataset", tmp_path / "reports")
    server = build_server(settings)

    tools = asyncio.run(server.list_tools())

    for tool in tools:
        assert tool.annotations is not None, f"{tool.name} no tiene ToolAnnotations"
        assert tool.annotations.read_only_hint is True, (
            f"{tool.name} no está marcada read_only_hint"
        )
        assert tool.annotations.destructive_hint is False


def test_no_write_operations_in_source():
    """P2-34 criterio explícito: sin INSERT/UPDATE/DELETE/put_object en el handler."""
    source = Path(__file__).resolve().parent.parent / "presentation" / "mcp_server.py"
    text = source.read_text(encoding="utf-8")
    assert not re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b|put_object", text, re.IGNORECASE)
    # Tampoco importa nada de storage/ (el único tier autorizado a tocar red/DB).
    assert "storage.db" not in text
    assert "storage.object_store" not in text


def test_get_dataset_summary_counts_real_data(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "dataset"
    _write_dataset(dataset_dir / "annotations")
    settings = _settings(monkeypatch, dataset_dir, tmp_path / "reports")
    server = build_server(settings)

    result = result_json(call(server, "get_dataset_summary"))

    assert result["total_images"] == 3
    assert result["total_annotations"] == 3
    assert result["images_per_category"] == {"dog": 2, "cat": 1}


def test_get_quality_report_available_when_file_exists(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    quality = {"schema_version": "1.0", "dataset_version": "x", "status": "passed", "checks": []}
    (reports_dir / "quality.json").write_text(json.dumps(quality), encoding="utf-8")
    settings = _settings(monkeypatch, tmp_path / "dataset", reports_dir)
    server = build_server(settings)

    result = result_json(call(server, "get_quality_report"))

    assert result["available"] is True
    assert result["data"]["status"] == "passed"


@pytest.mark.parametrize(
    "tool_name", ["get_quality_report", "get_splits_report", "get_versions_report"]
)
def test_report_tools_report_unavailable_instead_of_crashing(tmp_path, monkeypatch, tool_name):
    settings = _settings(monkeypatch, tmp_path / "dataset", tmp_path / "reports")
    server = build_server(settings)

    result = result_json(call(server, tool_name))

    assert result["available"] is False
    assert "reason" in result


def test_get_check_result_finds_an_existing_check(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    quality = {
        "schema_version": "1.0",
        "dataset_version": "x",
        "status": "warning",
        "checks": [
            {
                "check_name": "max_imbalance_ratio",
                "passed": False,
                "metric_value": 2.0,
                "details": {},
                "action": "warn",
            }
        ],
    }
    (reports_dir / "quality.json").write_text(json.dumps(quality), encoding="utf-8")
    settings = _settings(monkeypatch, tmp_path / "dataset", reports_dir)
    server = build_server(settings)

    result = result_json(call(server, "get_check_result", {"check_name": "max_imbalance_ratio"}))

    assert result["available"] is True
    assert result["data"]["metric_value"] == 2.0


def test_get_check_result_reports_unavailable_for_unknown_name(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    quality = {"schema_version": "1.0", "dataset_version": "x", "status": "passed", "checks": []}
    (reports_dir / "quality.json").write_text(json.dumps(quality), encoding="utf-8")
    settings = _settings(monkeypatch, tmp_path / "dataset", reports_dir)
    server = build_server(settings)

    result = result_json(call(server, "get_check_result", {"check_name": "no_existe"}))

    assert result["available"] is False
