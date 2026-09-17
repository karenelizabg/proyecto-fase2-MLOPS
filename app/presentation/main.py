import logging
import time

from sqlalchemy import text

from presentation import gate
from storage.db import get_engine
from storage.object_store import get_bucket_name, get_minio_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("dataset-quality-pipeline")


def _wait_for_dependencies(retries: int = 10, delay_seconds: float = 3.0) -> None:
    engine = get_engine()
    minio_client = get_minio_client()
    bucket = get_bucket_name()

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            minio_client.bucket_exists(bucket)
            logger.info("Conectado a MariaDB y a MinIO (bucket=%s).", bucket)
            return
        except Exception as error:  # noqa: BLE001 - reintento deliberado en el arranque
            logger.warning(
                "Intento %s/%s: dependencias aún no listas (%s).", attempt, retries, error
            )
            time.sleep(delay_seconds)

    raise RuntimeError("No se pudo conectar a MariaDB/MinIO tras varios intentos.")


def main() -> None:
    logger.info("dataset-quality-pipeline: arrancando.")
    _wait_for_dependencies()

    try:
        gate.run()
    except Exception:  # noqa: BLE001 - un quality.json roto no debe tumbar el contenedor
        logger.exception(
            "La compuerta de calidad no pudo correr al arrancar; "
            "el contenedor sigue vivo, reintenta con `python -m presentation.gate`."
        )

    logger.info("Listo. Splits y versionado (tiers 4-5) se implementan en frentes posteriores.")

    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
