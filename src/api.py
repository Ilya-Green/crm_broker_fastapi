from fastapi import APIRouter
from typing import List
import logging

from .services import api_get_statuses, api_client_create, api_client_list, api_get_types
from .models import Employee, Client
from .schemas import ClientCreate, ClientList


logger = logging.getLogger("api")

apiRouter = APIRouter(
    prefix="/client",
    tags=["clients"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


@apiRouter.get("/statuses")
async def get_statuses():
    return api_get_statuses()


@apiRouter.get("/types")
async def get_statuses():
    return api_get_types()


@apiRouter.post("/create/")
async def create_client(data: ClientCreate):
    logger.info(data)
    return api_client_create(data)


@apiRouter.post("/list/",
                    description="Returns list of clients. Patterns do not work yet",
                    # response_model=List[Client],
                    )
async def get_client_list(data: ClientList):
    return api_client_list(data)
