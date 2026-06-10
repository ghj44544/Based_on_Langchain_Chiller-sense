from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 200, "message": message, "data": data}


def error(message: str, code: int = 400, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )

