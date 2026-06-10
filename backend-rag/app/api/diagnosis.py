from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.response import error, success
from app.db.session import get_db
from app.services.diagnosis_service import run_diagnosis
from app.services.file_service import UnsupportedFileTypeError, save_upload_file
from app.services.model_predictor import MatlabEngineError, ModelNotFoundError
from app.services.rp1043_validator import ValidationError


router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.post("/upload")
async def upload_diagnosis_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        file_path = await save_upload_file(file)
        data = run_diagnosis(file_path, db)
        return success(data=data)
    except UnsupportedFileTypeError as exc:
        return error(str(exc), code=400)
    except ValidationError as exc:
        return error(str(exc), code=422, data=exc.summary)
    except ModelNotFoundError as exc:
        return error(str(exc), code=400)
    except MatlabEngineError as exc:
        return error(str(exc), code=400)
    except ValueError as exc:
        return error(str(exc), code=400)
