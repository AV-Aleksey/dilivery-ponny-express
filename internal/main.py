from fastapi import Depends, FastAPI
from internal.depends import get_pony_express_service
from internal.schemas.orders import OrderCalcRequest
from internal.services.pony_express import PonyExpress

app = FastAPI()

@app.post("/orders")
async def create_orders(
    body: OrderCalcRequest,
    pony_express_service: PonyExpress = Depends(get_pony_express_service)
):
    return await pony_express_service.get_calc_tariff(body)