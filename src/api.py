from fastapi import APIRouter
from typing import List

from .services import api_get_statuses, api_client_create
from .models import Employee, Client
from.schemas import ClientCreate


apiRouter = APIRouter(
    prefix="/client",
    tags=["clients"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


@apiRouter.get("/statuses")
async def get_statuses():
    return api_get_statuses()


@apiRouter.post("/create/")
async def create_client(data: ClientCreate):
    return api_client_create(data)
