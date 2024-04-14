from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from starlette.responses import JSONResponse

from src.platfrom_integration import update_platform_data

logger = logging.getLogger("database")

pt = APIRouter(
    prefix="/v1/pt",
    tags=["database"],
    # dependencies=[Depends(get_token_header)],
    include_in_schema=False,
)


# auth middleware


@pt.get("/synchronize-data")
async def create_trader():
    try:
        update_platform_data()
        return 'success'
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)

