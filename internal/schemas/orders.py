from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PackagesRequest(BaseModel):
    height: int
    length: int
    width: int
    weight: float


class OrderCalcRequest(BaseModel):
    from_location: str
    to_location: str
    packages: PackagesRequest


class OrderCalcResponse(BaseModel):
    courier_service: str  # PONY_EXPRESS
    courier_service_rating: Optional[int | None] = None
    price: int  # cумма заказа
    delivery_time_in_day: int  # скор доставки в днях
    pickup_day: datetime  # день получения
    delivery_day: datetime  # день доставки
    delivery_rate: str  # Супер-экспресс до 14 дверь-дверь
    delivery_rate_description: Optional[str | None] = None
