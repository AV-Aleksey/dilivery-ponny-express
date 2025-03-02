import pytz
import textwrap
import xmltodict

from zeep import Client
from typing import Optional
from pydantic import BaseModel
from app.config import settings
from zeep.exceptions import Fault
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime, timedelta

app = FastAPI()

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
    courier_service: str # PONY_EXPRESS
    courier_service_rating: Optional[int | None] = None
    price: int #cумма заказа
    delivery_time_in_day: int # скор доставки в днях
    pickup_day: datetime # день получения
    delivery_day: datetime # день доставки
    delivery_rate: str # Супер-экспресс до 14 дверь-дверь
    delivery_rate_description: Optional[str | None] = None 

def apiResponse(offer):
    def calc_period(days):
        moscow_tz = pytz.timezone('Europe/Moscow')
        send_date = datetime.now(moscow_tz)
        receive_date = send_date + timedelta(days=days)

        return send_date, receive_date

    pickup_day, delivery_day = calc_period(int(offer['MinTerm']))

    order = {
        "courier_service": "PONY_EXPRESS",
        "courier_service_rating": None,
        "price": int(float(offer['Sum'])),
        "delivery_time_in_day": int(offer['MinTerm']),
        "pickup_day": pickup_day,
        "delivery_day": delivery_day,
        "delivery_rate": offer['Description'],
        "delivery_rate_description": offer['DeliveryMethod']
    }

    return OrderCalcResponse(**order)

def createBody(from_location: str, to_location: str, length: int, width: int, height: int, weight: int):
    # Заменить после расширения payload
    from_street = 'ул.Ленина, д.1'
    to_street = 'ул.Ленина, д.1'

    return textwrap.dedent(f'''\
        <?xml version="1.0" encoding="utf-8"?>
        <Request xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="OrderRequest">
            <Mode>Calculation</Mode> <!--Required-->
            <OrderList> <!--Required-->
                <Order> <!--Required-->
                    <ServiceList> <!--Required-->
                        <Service xsi:type="DeliveryService"> <!--Required-->
                            <Sender> <!--Required-->
                                <Address> <!--Required-->
                                    <City>{from_location}</City> <!--Required-->
                                    <StreetAddress>{from_street}</StreetAddress> <!--Required-->
                                </Address>
                            </Sender>
                            <Recipient> <!--Required-->
                                <Address> <!--Required-->
                                    <City>{to_location}</City> <!--Required-->
                                    <StreetAddress>{to_street}</StreetAddress> <!--Required-->
                                </Address>
                            </Recipient>
                            <CargoList> <!--Required-->
                                <Cargo>
                                    <Dimentions>
                                        <Length>{length}</Length>
                                        <Width>{width}</Width>
                                        <Height>{height}</Height>
                                    </Dimentions>
                                    <Weight>{weight}</Weight>
                                </Cargo>
                            </CargoList>
                        </Service>
                    </ServiceList>
                </Order>
            </OrderList>
        </Request>
    ''')

# Безопасно возвращает данные из удаленного источника или информацию об ошибке (api в случае ошибки возвращает 200)
def getSafeData(data):
    status = data.get('Response', {}).get('OrderList', {}).get('Order', {}).get('StatusList')

    try:
        if 'OrderList' in data.get('Response', {}):
            return {
                "error": None,
                "data": data['Response']['OrderList']['Order']['ServiceList']['Service']['Calculation']['DeliveryRateSet']['DeliveryRate']
            }
        else:
            # todo - нужно еще подумать как обработать исключение, если данных нет по указанным ключам
            raise HTTPException(status_code=500, detail={"error": "SOAP Fault", "message": str(status)})
    except:
        raise HTTPException(status_code=500, detail={"error": "SOAP Fault", "message": str(status)})


@app.get("/orders")
async def get_zeep(
    from_location: str = Query(..., description="Город отправления"),
    to_location: str = Query(..., description="Город назначения"),
    height: int = Query(..., description="Высота упаковки"),
    length: int = Query(..., description="Длина упаковки"),
    width: int = Query(..., description="Ширина упаковки"),
    weight: float = Query(..., description="Вес упаковки"),
):
    client = Client(wsdl=settings.PONY_API_URL)

    chk_query = {
        'accesskey': settings.PONY_API_KEY,
        'requestBody': createBody(from_location=from_location, to_location=to_location, height=height, weight=int(weight), width=width, length=length)
    }

    try:
        response = client.service.SubmitRequest(**chk_query)
 
        data = xmltodict.parse(response)

        offers = getSafeData(data=data)

        return { "data": [apiResponse(item) for item in offers["data"]] };
    except Fault as err:
        print(f"SOAP Fault: {err}")