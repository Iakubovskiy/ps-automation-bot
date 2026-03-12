import logging
import io
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self, org=None):
        self.endpoint = (org.s3_endpoint if org and org.s3_endpoint else settings.MINIO_ENDPOINT)
        self.access_key = (org.s3_access_key if org and org.s3_access_key else settings.MINIO_ACCESS_KEY)
        self.secret_key = (org.s3_secret_key if org and org.s3_secret_key else settings.MINIO_SECRET_KEY)
        self.bucket_name = (org.s3_bucket_name or str(org.id) if org else settings.MINIO_BUCKET_NAME).lower().replace("_", "-")
        
        self.use_ssl = settings.MINIO_USE_SSL
        protocol = "https" if self.use_ssl else "http"

        self._client = boto3.client(
            "s3",
            endpoint_url=f"{protocol}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def _ensure_bucket(self) -> None:
        """Перевірка та створення бакета."""
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            logger.info("Creating S3 bucket: %s", self.bucket_name)
            self._client.create_bucket(Bucket=self.bucket_name)

    def upload_fileobj(self, file_data: io.BytesIO, s3_key: str) -> str:
        """Завантаження файлу безпосередньо з пам'яті."""
        self._ensure_bucket()
        file_data.seek(0)
        self._client.upload_fileobj(file_data, self.bucket_name, s3_key)
        logger.info("Uploaded to s3://%s/%s", self.bucket_name, s3_key)
        return f"{self.bucket_name}/{s3_key}"

    def download_file(self, s3_path: str, local_path: str) -> None:
        """Завантажує файл з S3 на локальний диск.

        Args:
            s3_path: Шлях у форматі 'bucket-name/products/uuid/file.jpg'
                     або 'products/uuid/file.jpg'
            local_path: Абсолютний шлях на диску, куди зберегти файл.
        """
        prefix = f"{self.bucket_name}/"
        if s3_path.startswith(prefix):
            s3_key = s3_path[len(prefix):]
        else:
            s3_key = s3_path

        self._client.download_file(self.bucket_name, s3_key, local_path)
        logger.info("Downloaded s3://%s/%s to %s", self.bucket_name, s3_key, local_path)
