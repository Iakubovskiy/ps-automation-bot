"""Local file manager for temporary distribution assets (like photos for Playwright)."""
import logging
import os
import tempfile
from contextlib import asynccontextmanager

from asgiref.sync import sync_to_async

from modules.catalog.infrastructure.s3_service import S3Service
from modules.users.domain.organization import Organization

logger = logging.getLogger(__name__)


@asynccontextmanager
async def download_media_for_publishing(s3_paths: list[str], organization_id: str):
    """
    Асинхронний контекстний менеджер для завантаження фото з S3.
    Створює тимчасову папку, завантажує туди файли, віддає список локальних шляхів,
    а після виходу з блоку with — гарантовано видаляє папку з диска.
    """
    if not s3_paths:
        yield []
        return

    org = await Organization.objects.aget(id=organization_id)
    s3_service = S3Service(org=org)

    base_dir = "/app/media/temp_publish"
    os.makedirs(base_dir, exist_ok=True)

    temp_dir = tempfile.TemporaryDirectory(dir=base_dir, prefix="pub_")
    local_paths = []

    try:
        for s3_path in s3_paths:
            if not s3_path:
                continue

            file_name = os.path.basename(s3_path)
            local_path = os.path.join(temp_dir.name, file_name)

            await sync_to_async(s3_service.download_file)(s3_path, local_path)
            local_paths.append(local_path)

        logger.info("Завантажено %d файлів у %s", len(local_paths), temp_dir.name)

        # Передаємо керування назад (наприклад, у Playwright)
        yield local_paths

    finally:
        temp_dir.cleanup()
        logger.info("Тимчасову папку %s успішно видалено", temp_dir.name)
