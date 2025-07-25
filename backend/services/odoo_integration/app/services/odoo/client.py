import httpx
from exponential_core.exceptions import CustomAppException, OdooException
from exponential_core.logger import get_logger
from app.core.settings import settings
from app.services.odoo.exceptions import OdooCallException


logger = get_logger()


class AsyncOdooClient:
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self.jsonrpc_url = f"{url}/jsonrpc"
        self.uid = None
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=settings.HTTP_TIMEOUT_READ,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

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

        try:

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.jsonrpc_url, json=payload)
                data = response.json()

                if "error" in data:
                    message = (
                        data.get("error", {})
                        .get("data", {})
                        .get("message", "Error inesperado")
                    )

                    logger.error(f"Error al autenticar con odoo: {message}")

                    raise OdooException(
                        f"Error autenticando con Odoo: {message}",
                        status_code=502,
                    )

                if "result" not in data or not data["result"]:
                    raise OdooException(
                        "Credenciales inválidas para Odoo", status_code=401
                    )

                logger.info("Autenticación exitosa con Odoo")
                self.uid = data["result"]
                return self.uid

        except OdooException as e:
            raise e

        except httpx.RequestError as e:
            logger.error(f"Error de red al autenticar con Odoo: {e}")
            raise OdooException("Fallo de red al autenticar con Odoo", status_code=504)

        except ValueError as e:
            logger.exception("La respuesta de Odoo no es JSON válido")
            raise OdooException("Respuesta inválida desde Odoo", status_code=502)

        except Exception as e:
            logger.exception("Fallo inesperado al autenticar con Odoo")
            raise CustomAppException(
                "Error inesperado al autenticar con Odoo", data={"error": str(e)}
            )

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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.jsonrpc_url, json=payload)

        try:
            data = response.json()
            if "error" in data:
                logger.error(f"Odoo error: {data['error']}")
                # Puedes extraer más información si lo deseas:
                error_message = data["error"]["data"].get(
                    "message", "Error desconocido en Odoo"
                )
                raise OdooCallException(
                    message=f"Error en Odoo: {error_message}",
                    odoo_error=data["error"],
                    status_code=502,
                )
            return data.get("result")
        except OdooCallException as oe:
            logger.error(f"Excepción OdooCallException: {oe}")
            raise
        except Exception as e:
            logger.exception("Fallo en la llamada JSON-RPC a Odoo")
            raise CustomAppException(
                "Error inesperado al comunicarse con Odoo",
                data={"error": str(e)},
                status_code=500,
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
        """
        Consulta la metadata de los campos del modelo en Odoo.
        Por defecto retorna 'string', 'help', 'type' y 'required' para cada campo.
        - model: nombre del modelo Odoo
        - attributes: lista opcional de atributos extra a incluir en el resultado
        """
        default_attrs = ["string", "help", "type", "required"]
        return await self.call(
            model,
            "fields_get",
            [],
            {"attributes": attributes or default_attrs},
        )
