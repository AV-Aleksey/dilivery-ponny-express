import textwrap
import xmltodict

from zeep import AsyncClient
from internal.config import settings
from zeep.exceptions import Fault
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from internal.schemas.orders import OrderCalcRequest, OrderCalcResponse

def apiResponse(offer):
    def calc_period(days):
        moscow_tz = timezone(timedelta(hours=3))
        send_date = datetime.now(moscow_tz)
        receive_date = send_date + timedelta(days=days)

        return send_date, receive_date

    pickup_day, delivery_day = calc_period(int(offer["MinTerm"]))

    return OrderCalcResponse(
        courier_service="PONY_EXPRESS",
        courier_service_rating=None,
        price=int(float(offer["Sum"])),
        delivery_time_in_day=int(offer["MinTerm"]),
        pickup_day=pickup_day,
        delivery_day=delivery_day,
        delivery_rate=offer["Description"],
        delivery_rate_description=offer["DeliveryMethod"],
    )


def createBody(params: OrderCalcRequest):
    # Заменить после расширения payload
    from_street = "ул.Ленина, д.1"
    to_street = "ул.Ленина, д.1"

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <Request xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="OrderRequest">
            <Mode>Calculation</Mode> <!--Required-->
            <OrderList> <!--Required-->
                <Order> <!--Required-->
                    <ServiceList> <!--Required-->
                        <Service xsi:type="DeliveryService"> <!--Required-->
                            <Sender> <!--Required-->
                                <Address> <!--Required-->
                                    <City>{params.from_location}</City> <!--Required-->
                                    <StreetAddress>{from_street}</StreetAddress> <!--Required-->
                                </Address>
                            </Sender>
                            <Recipient> <!--Required-->
                                <Address> <!--Required-->
                                    <City>{params.to_location}</City> <!--Required-->
                                    <StreetAddress>{to_street}</StreetAddress> <!--Required-->
                                </Address>
                            </Recipient>
                            <CargoList> <!--Required-->
                                <Cargo>
                                    <Dimentions>
                                        <Length>{params.packages.length}</Length>
                                        <Width>{params.packages.width}</Width>
                                        <Height>{params.packages.height}</Height>
                                    </Dimentions>
                                    <Weight>{int(params.packages.weight)}</Weight>
                                </Cargo>
                            </CargoList>
                        </Service>
                    </ServiceList>
                </Order>
            </OrderList>
        </Request>
    """)

class PonyExpress:
    async def get_calc_tariff(self, body: OrderCalcRequest):
        async with AsyncClient(wsdl=settings.PONY_API_URL) as client:
            try:
                response = await client.service.SubmitRequest(accesskey=settings.PONY_API_KEY, requestBody=createBody(body))

                data = xmltodict.parse(response)

                status = (
                    data.get("Response", {}).get("OrderList", {}).get("Order", {}).get("StatusList")
                )

                if 'ErrorCode' in status.get("OrderStatus", {}):
                    raise HTTPException(status_code=500, detail={"error": "SOAP Fault", "message": str(status)})
                
                if "OrderList" not in data.get("Response", {}):
                    raise HTTPException(status_code=500, detail={"error": "SOAP Fault", "message": str(status)})
                
                offers = data["Response"]["OrderList"]["Order"]["ServiceList"]["Service"]["Calculation"]["DeliveryRateSet"]["DeliveryRate"]

                return [apiResponse(item) for item in offers]
            except Fault as err:
                print(f"SOAP Fault: {err}")
