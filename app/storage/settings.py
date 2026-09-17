"""Tier 5 — configuración de infraestructura y política de calidad.

Único módulo autorizado a leer `.env`/variables de entorno (ver la regla de
la compuerta de acoplamiento en `app/tests/test_architecture.py`).
`quality.yaml` entra por el mismo mecanismo de fuentes de `pydantic-settings`,
así que una variable de entorno faltante o un umbral roto en la política se
rechazan aquí, con un error que nombra el campo, antes de que cualquier otro
tier los use.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from policies.models import QualityPolicy

APP_ROOT = Path(__file__).resolve().parent.parent


class YamlSectionSource(PydanticBaseSettingsSource):
    """Fuente de `pydantic-settings` que anida un YAML completo bajo un campo."""

    def __init__(self, settings_cls: type[BaseSettings], *, field_name: str, yaml_path: Path):
        super().__init__(settings_cls)
        self._field_name = field_name
        self._yaml_path = yaml_path

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        if not self._yaml_path.exists():
            return {}
        raw = yaml.safe_load(self._yaml_path.read_text(encoding="utf-8"))
        return {self._field_name: raw}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(APP_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    minio_endpoint: str
    minio_port: int
    minio_access_key: str
    minio_secret_key: str
    minio_use_ssl: bool = False
    minio_bucket: str

    quality: QualityPolicy

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlSectionSource(
                settings_cls,
                field_name="quality",
                yaml_path=APP_ROOT / "policies" / "quality.yaml",
            ),
            file_secret_settings,
        )
