from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.utils.file_utils import ensure_dir, unique_filename


ALLOWED_SUFFIXES = {".xlsx", ".xls", ".csv"}


class UnsupportedFileTypeError(ValueError):
    pass


async def save_upload_file(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise UnsupportedFileTypeError("仅支持 .xlsx、.xls、.csv 文件")

    settings = get_settings()
    upload_dir = ensure_dir(settings.upload_path)
    file_path = upload_dir / unique_filename(file.filename or f"upload{suffix}")

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)
    return file_path

