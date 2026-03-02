"""S3 / MinIO file service for the Catalog module.

Handles uploading, moving, and deleting product media files
between local storage and the organization's S3 bucket.
"""
import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3Service:
    """MinIO/S3 file operations for product media."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket_name: str | None = None,
        use_ssl: bool | None = None,
    ):
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket_name = bucket_name or settings.MINIO_BUCKET_NAME
        self.use_ssl = use_ssl if use_ssl is not None else settings.MINIO_USE_SSL

        protocol = "https" if self.use_ssl else "http"
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{protocol}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            logger.info("Creating S3 bucket: %s", self.bucket_name)
            self._client.create_bucket(Bucket=self.bucket_name)

    def upload_file(self, local_path: str, s3_key: str) -> str:
        """Upload a local file to S3 and return the S3 key.

        Args:
            local_path: Absolute path to the local file.
            s3_key: Target key in the S3 bucket (e.g. "products/<uuid>/photo_1.jpg").

        Returns:
            The S3 key of the uploaded file.
        """
        self._client.upload_file(local_path, self.bucket_name, s3_key)
        logger.info("Uploaded %s → s3://%s/%s", local_path, self.bucket_name, s3_key)
        return s3_key

    def upload_product_media(
        self,
        product_id: str,
        local_paths: list[str],
    ) -> list[str]:
        """Upload multiple media files for a product.

        Files are stored under products/<product_id>/<filename>.

        Args:
            product_id: UUID of the product.
            local_paths: List of absolute paths to local files.

        Returns:
            List of S3 keys for the uploaded files.
        """
        s3_keys = []
        for local_path in local_paths:
            filename = Path(local_path).name
            s3_key = f"products/{product_id}/{filename}"
            self.upload_file(local_path, s3_key)
            s3_keys.append(s3_key)
        return s3_keys

    def delete_file(self, s3_key: str) -> None:
        """Delete a file from S3."""
        self._client.delete_object(Bucket=self.bucket_name, Key=s3_key)
        logger.info("Deleted s3://%s/%s", self.bucket_name, s3_key)

    def get_url(self, s3_key: str) -> str:
        """Generate a URL for accessing a file in S3."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket_name}/{s3_key}"
