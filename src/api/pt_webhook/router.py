from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.api.pt_webhook.schemas import OrderUpdate, TransactionUpdate
from src.api.pt_webhook.services import create_trader_webhook, create_order_webhook, create_transaction_webhook, \
    update_whitelist, update_order_webhook, update_transaction_webhook
from src.models import Trader, Order, Transaction
from src.platfrom_integration import update_platform_data

logger = logging.getLogger("database")

WHITELIST = ["127.0.0.1"]


def check_ip_whitelist(request: Request):
    client_ip = request.headers.get('CF-Connecting-IP') or request.client.host
    if client_ip not in WHITELIST:
        raise HTTPException(status_code=404, detail="Not Found")


pt = APIRouter(
    prefix="/v1/pt",
    include_in_schema=False,
    tags=["pt"],
    dependencies=[Depends(check_ip_whitelist)],
)


@pt.get("/update-whitelist")
async def update_whitelist_pt():
    try:
        WHITELIST.clear()
        ips = update_whitelist()
        ips.append("127.0.0.1")
        WHITELIST.extend(ips)
        return JSONResponse(content={"message": "Whitelist updated successfully"}, status_code=200)
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.get("/synchronize-data")
async def synchronize_data():
    try:
        update_platform_data()
        return 'success'
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/trader/create")
async def create_trader(trader: Trader):
    try:
        create_trader_webhook(trader)
        return JSONResponse(content={"message": f"Successfully created trader id:{trader.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/trader/update")
async def update_trader(trader: Trader):
    try:
        create_trader_webhook(trader)
        return JSONResponse(content={"message": f"Successfully updated trader id:{trader.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/order/create")
async def create_order(order: Order):
    try:
        create_order_webhook(order)
        return JSONResponse(content={"message": f"Successfully created order id:{order.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/order/update")
async def update_order(order: OrderUpdate):
    try:
        update_order_webhook(order)
        return JSONResponse(content={"message": f"Successfully created order id:{order.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/transaction/create")
async def create_transaction(transaction: Transaction):
    try:
        create_transaction_webhook(transaction)
        return JSONResponse(content={"message": f"Successfully created transaction id:{transaction.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)


@pt.post("/transaction/update")
async def update_transaction(transaction: TransactionUpdate):
    try:
        update_transaction_webhook(transaction)
        return JSONResponse(content={"message": f"Successfully created transaction id:{transaction.id}"}, status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Произошла ошибка: {str(e)}"}, status_code=500)

