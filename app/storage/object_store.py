import os

from minio import Minio


def get_minio_client() -> Minio:
    return Minio(
        f"{os.environ['MINIO_ENDPOINT']}:{os.environ['MINIO_PORT']}",
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=os.environ.get("MINIO_USE_SSL", "false").lower() == "true",
    )


def get_bucket_name() -> str:
    return os.environ["MINIO_BUCKET"]
