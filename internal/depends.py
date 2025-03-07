from internal.services.pony_express import PonyExpress

pony_express_service = PonyExpress()


async def get_pony_express_service() -> PonyExpress:
    return pony_express_service
