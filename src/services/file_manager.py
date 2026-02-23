"""Module for managing local files and directories."""
import os
import uuid
from pathlib import Path

MEDIA_BASE_PATH = Path("media")

def generate_item_uuid() -> str:
    """Generate a unique identifier for a new item."""
    return str(uuid.uuid4())

def ensure_directory_exists(item_uuid: str) -> Path:
    """Create a directory for the item if it doesn't exist."""
    path = MEDIA_BASE_PATH / item_uuid
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_file_path(item_uuid: str, filename: str) -> str:
    """Return the full path where the file should be saved."""
    directory = ensure_directory_exists(item_uuid)
    return str(directory / filename)