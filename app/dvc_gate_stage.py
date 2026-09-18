"""Wrapper del stage `quality_gate` de `dvc.yaml` (P2-42).

DVC ejecuta `cmd` a través del shell del sistema operativo (`cmd.exe` en
Windows), que no soporta la sintaxis `VAR=valor comando` de bash/sh usada
en los ejemplos de `presentation/README.md`. Este script fija las mismas
variables con `os.environ` antes de invocar `presentation.gate.main()`,
así el stage funciona igual en Windows/Mac/Linux sin depender de sintaxis
de shell específica de una plataforma.

`DATABASE_URL`/`MINIO_*` son campos requeridos por `storage.Settings`
(tier 5 agrupa toda la config junta) pero `gate.py` nunca los usa — no
abre conexiones a MariaDB ni MinIO — así que un valor placeholder basta.

Llama a `gate.run()`, no a `gate.main()`: `run()` siempre escribe
`quality.json` y no decide exit code (ver el propio docstring de
`gate.py`); `main()` sí devuelve 1 cuando `status == "failed"`, pensado
para un paso de CI que bloquee expresamente, no para `dvc repro`. Si este
stage usara `main()`, "el dataset todavía no cumple la meta" (un estado
real y esperado, ver `app/presentation/README.md`) impediría regenerar
`dvc.lock` — confundiría "¿corrió el cómputo?" con "¿pasó la calidad?".
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

os.environ.setdefault("DATABASE_URL", "unused")
os.environ.setdefault("MINIO_ENDPOINT", "unused")
os.environ.setdefault("MINIO_PORT", "9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "unused")
os.environ.setdefault("MINIO_SECRET_KEY", "unused")
os.environ.setdefault("MINIO_BUCKET", "unused")
os.environ.setdefault("DATASET_DIR", str(REPO_ROOT / "data" / "raw"))
os.environ.setdefault("REPORTS_DIR", str(REPO_ROOT / "reports"))

import logging  # noqa: E402 - env vars must be set first

from presentation.gate import run  # noqa: E402 - env vars must be set first

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
    sys.exit(0)
