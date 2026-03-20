"""
MinIO client wrapper.
"""
from django.conf import settings
from minio import Minio
from minio.error import S3Error
import io


class MinIOClient:
    _instance = None

    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            import logging
            logging.getLogger(__name__).error(f"MinIO bucket init error: {e}")

    def put_object(self, object_key: str, data, length: int, content_type: str = "application/octet-stream"):
        self.client.put_object(self.bucket, object_key, data, length, content_type=content_type)

    def get_object(self, object_key: str) -> bytes:
        response = self.client.get_object(self.bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def put_bytes(self, object_key: str, data: bytes, content_type: str = "application/octet-stream"):
        self.client.put_object(
            self.bucket, object_key,
            io.BytesIO(data), len(data),
            content_type=content_type,
        )

    def copy_object(self, dest_key: str, src_key: str):
        from minio.commonconfig import CopySource
        self.client.copy_object(self.bucket, dest_key, CopySource(self.bucket, src_key))
        self.client.remove_object(self.bucket, src_key)

    def delete_object(self, object_key: str):
        self.client.remove_object(self.bucket, object_key)

    def presigned_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        from datetime import timedelta
        return self.client.presigned_get_object(
            self.bucket, object_key,
            expires=timedelta(seconds=expires_seconds),
        )


# Singleton
