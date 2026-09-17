import pytest
from pydantic import ValidationError

from storage.settings import Settings

REQUIRED_ENV = {
    "DATABASE_URL": "mysql+pymysql://user:pass@localhost/db",
    "MINIO_ENDPOINT": "localhost",
    "MINIO_PORT": "9000",
    "MINIO_ACCESS_KEY": "ak",
    "MINIO_SECRET_KEY": "sk",
    "MINIO_BUCKET": "bucket",
    "DATASET_DIR": "/data/raw",
    "REPORTS_DIR": "/reports",
}


def set_required_env(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)


def test_settings_load_env_and_real_yaml_files(monkeypatch):
    set_required_env(monkeypatch)
    settings = Settings()
    assert settings.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert settings.minio_port == 9000
    assert settings.minio_use_ssl is False
    assert settings.quality.min_images_per_class.threshold == 300


@pytest.mark.parametrize("missing", list(REQUIRED_ENV))
def test_missing_env_var_is_rejected_naming_the_field_not_a_key_error(monkeypatch, missing):
    set_required_env(monkeypatch)
    monkeypatch.delenv(missing, raising=False)
    with pytest.raises(ValidationError, match=missing.lower()):
        Settings()


def test_non_numeric_port_is_rejected(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("MINIO_PORT", "not-a-port")
    with pytest.raises(ValidationError, match="minio_port"):
        Settings()
