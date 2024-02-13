from fastapi import APIRouter
import logging

from src.api.v1.services import api_client_create, api_client_list
from src.api.v1.schemas import ClientListIn, ClientCreateIn, ClientCreateOut, ClientListOut, ClientListInPydantic

logger = logging.getLogger("api")

affApiV1 = APIRouter(
    prefix="/v1/client",
    tags=["integration"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
    responses={
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {"detail": "there is no such auth_key"}
                }
            },
        }
    }
)


@affApiV1.post("/create/", response_model=ClientCreateOut,
               responses={
                   403: {
                       "description": "Forbidden",
                       "content": {
                           "application/json": {
                               "example": {"detail": "Duplicate"}
                           }
                       },
                   }
               }
               )
async def create_client(data: ClientCreateIn):
    logger.info(data)
    return api_client_create(data)


@affApiV1.post("/list/",
                    description="Returns list of clients",
                    response_model=ClientListOut,
                    )
async def get_client_list(data: ClientListInPydantic):
    return api_client_list(data)
