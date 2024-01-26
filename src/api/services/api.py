from fastapi import APIRouter

from src.api.services.services import api_get_statuses, api_get_types

statusesRouter = APIRouter(
    prefix="/v1/client",
    include_in_schema=False
)


@statusesRouter.get("/statuses")
async def get_statuses():
    return api_get_statuses()


@statusesRouter.get("/types")
async def get_statuses():
    return api_get_types()
