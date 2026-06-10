import os
import tempfile
import uuid
from pathlib import Path


test_db = Path(tempfile.gettempdir()) / f"chiller_sense_rag_test_{uuid.uuid4().hex}.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{test_db.as_posix()}")
