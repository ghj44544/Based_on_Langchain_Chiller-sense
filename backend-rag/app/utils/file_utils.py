import re
from pathlib import Path
from uuid import uuid4


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    sanitized = re.sub(r"[^A-Za-z0-9_.\-\u4e00-\u9fff]", "_", name)
    return sanitized or f"upload_{uuid4().hex}"


def unique_filename(filename: str) -> str:
    path = Path(safe_filename(filename))
    return f"{path.stem}_{uuid4().hex[:10]}{path.suffix}"

