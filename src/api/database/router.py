from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from starlette.responses import JSONResponse

from src.api.database.services import api_upload_database, api_check_database

logger = logging.getLogger("database")

db = APIRouter(
    prefix="/v1/database",
    tags=["database"],
    # dependencies=[Depends(get_token_header)],
    include_in_schema=False,
)


@db.post("/upload/")
async def upload_database(
        department_id: Optional[int] = None,
        desk_id: Optional[int] = None,
        responsible_id: Optional[int] = None,
        affiliate_id: Optional[int] = None,
        new_affiliate_name: Optional[str] = None,
        funnel_name: Optional[str] = None,
        file: UploadFile = File(...),
        # check: UploadFile = File(None)
):

    try:
        return await api_upload_database(
            department_id=department_id,
            desk_id=desk_id,
            responsible_id=responsible_id,
            affiliate_id=affiliate_id,
            new_affiliate_name=new_affiliate_name,
            funnel_name=funnel_name,
            file=file
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@db.post("/check/")
async def check_detabase(file: UploadFile = File(...)):
    return await api_check_database(file)

