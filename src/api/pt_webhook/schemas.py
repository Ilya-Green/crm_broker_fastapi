from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class TransactionUpdate(SQLModel):
    id: str = Field(primary_key=True)
    content: Optional[str] = Field()
    createdAt: Optional[datetime] = Field()
    dirName: Optional[str] = Field()
    type: Optional[str] = Field()
    value: Optional[float] = Field()
    v: Optional[int] = Field()

    trader_id: Optional[str] = Field()


class OrderUpdate(SQLModel):
    wid: Optional[str] = Field()
    id: str = Field(primary_key=True)
    asset_name: Optional[str] = Field()
    amount: Optional[float] = Field()
    opening_price: Optional[float] = Field()
    pledge: Optional[float] = Field()
    type: Optional[str] = Field()
    is_closed: Optional[bool] = Field()
    created_at: Optional[datetime] = Field()
    take_profit: Optional[float] = Field()
    stop_loss: Optional[float] = Field()
    auto_close: Optional[bool] = Field()
    v: Optional[int] = Field()
    closed_at: Optional[datetime] = Field()
    closed_price: Optional[float] = Field()
    profit: Optional[float] = Field()
    spread: Optional[float] = Field()

    user_id: Optional[str] = Field()
