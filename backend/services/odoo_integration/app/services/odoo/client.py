import httpx
from exponential_core.exceptions.types import OdooException
from exponential_core.logger import get_logger

logger = get_logger()


class AsyncOdooClient:
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self.jsonrpc_url = f"{url}/jsonrpc"
        self.uid = None

    async def authenticate(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, self.username, self.api_key, {}],
            },
            "id": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.jsonrpc_url, json=payload)

        if response.status_code != 200 or "result" not in response.json():
            raise OdooException("Fallo al autenticar con Odoo")

        result = response.json()["result"]
        if not result:
            raise OdooException("Credenciales inválidas para Odoo", status_code=401)

        logger.info("Autenticación exitosa con Odoo")
        self.uid = result
        return self.uid

    async def call(self, model, method, args=None, kwargs=None):
        if self.uid is None:
            await self.authenticate()

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    self.uid,
                    self.api_key,
                    model,
                    method,
                    args or [],
                    kwargs or {},
                ],
            },
            "id": 1,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.jsonrpc_url, json=payload)

        try:
            data = response.json()
            if "error" in data:
                logger.error(f"Odoo error: {data['error']}")
                raise OdooException(f"OdooError: {data['error']['data']['message']}")
            return data.get("result")
        except Exception as e:
            logger.exception("Fallo en la llamada JSON-RPC a Odoo")
            raise OdooException(
                "Error inesperado al comunicarse con Odoo", data={"error": str(e)}
            )

    async def create(self, model, data):
        return await self.call(model, "create", [data])

    async def read(self, model, domain, fields=None):
        return await self.call(model, "search_read", [domain], {"fields": fields or []})

    async def update(self, model, ids, data):
        return await self.call(model, "write", [ids, data])

    async def delete(self, model, ids):
        return await self.call(model, "unlink", [ids])

    async def fields_get(self, model, attributes=None):
        return await self.call(
            model,
            "fields_get",
            [],
            {"attributes": attributes or ["string", "help", "type"]},
        )
