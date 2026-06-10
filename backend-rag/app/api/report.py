from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.response import error, success
from app.db.session import get_db
from app.services.report_service import (
    ReportFileError,
    ReportFormatError,
    ReportNotFoundError,
    build_report_export_data,
    find_latest_report,
    generate_report_file,
    get_report_media_type,
    get_report_file,
)


router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate/{diagnosis_id}")
def generate_report(
    diagnosis_id: int,
    report_format: str = "md",
    db: Session = Depends(get_db),
):
    try:
        report_path = generate_report_file(diagnosis_id, db, report_format=report_format)
    except ReportNotFoundError as exc:
        return error(str(exc), code=404)
    except ReportFormatError as exc:
        return error(str(exc), code=400)
    return success(data=build_report_export_data(report_path))


@router.get("/latest/{diagnosis_id}")
def latest_report(diagnosis_id: int, report_format: str | None = None):
    try:
        report_path = find_latest_report(diagnosis_id, report_format=report_format)
    except ReportNotFoundError as exc:
        return error(str(exc), code=404)
    except ReportFormatError as exc:
        return error(str(exc), code=400)
    return success(data=build_report_export_data(report_path))


@router.get("/download/latest/{diagnosis_id}")
def download_latest_report(diagnosis_id: int, report_format: str | None = None):
    try:
        report_path = find_latest_report(diagnosis_id, report_format=report_format)
    except ReportNotFoundError as exc:
        return error(str(exc), code=404)
    except ReportFormatError as exc:
        return error(str(exc), code=400)
    return FileResponse(
        path=report_path,
        media_type=get_report_media_type(report_path),
        filename=report_path.name,
    )


@router.get("/download/{filename}")
def download_report(filename: str):
    try:
        report_path = get_report_file(filename)
    except ReportNotFoundError as exc:
        return error(str(exc), code=404)
    except ReportFileError as exc:
        return error(str(exc), code=400)
    return FileResponse(
        path=report_path,
        media_type=get_report_media_type(report_path),
        filename=report_path.name,
    )
