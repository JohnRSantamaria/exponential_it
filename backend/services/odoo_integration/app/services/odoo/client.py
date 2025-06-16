import xmlrpc.client
import socket


from app.services.odoo.utils import parse_fault_string
from exponential_core.logger import configure_logging
from exponential_core.exceptions.types import OdooException

logger = configure_logging()


class OdooClient:
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        logger.info(f"Iniciando cliente Odoo para usuario '{username}' en DB '{db}'")
        self.uid = self._authenticate()
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    def _authenticate(self):
        try:
            logger.debug("Autenticando con Odoo...")
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            uid = common.authenticate(self.db, self.username, self.api_key, {})
            if not uid:
                logger.warning("Falló la autenticación con Odoo.")
                raise OdooException("Autenticación fallida con Odoo", status_code=401)
            logger.info("Autenticación exitosa con Odoo.")
            return uid
        except socket.error as e:
            logger.error(f"Conexión fallida al servidor Odoo: {e}")
            raise OdooException(
                "No se pudo conectar al servidor de Odoo",
                data={"error": str(e)},
                status_code=503,
            )
        except Exception as e:
            logger.exception("Error inesperado al autenticar con Odoo.")
            raise OdooException(
                "Error inesperado al autenticar", data={"error": str(e)}
            )

    def _handle_rpc(self, fn):
        try:
            return fn()
        except xmlrpc.client.Fault as e:
            msg = parse_fault_string(e.faultString)
            logger.warning(f"OdooFault: {msg}")
            raise OdooException(f"Odoo Fault: {msg}")
        except socket.timeout:
            logger.error("Timeout al comunicarse con Odoo.")
            raise OdooException("Conexión a Odoo agotada (timeout)", status_code=504)
        except socket.error as e:
            logger.error(f"Error de red al comunicarse con Odoo: {e}")
            raise OdooException(
                "Error de red al comunicarse con Odoo",
                data={"error": str(e)},
                status_code=503,
            )
        except Exception as e:
            logger.exception("Error inesperado al ejecutar operación en Odoo.")
            raise OdooException(
                "Error inesperado al ejecutar operación en Odoo",
                data={"error": str(e)},
                status_code=500,
            )

    def create(self, model, data):
        logger.debug(f"Creando registro en {model}: {data}")
        return self._handle_rpc(
            lambda: self.models.execute_kw(
                self.db, self.uid, self.api_key, model, "create", [data]
            )
        )

    def read(self, model, domain, fields=None):
        logger.debug(
            f"Leyendo registros de {model} con dominio {domain} y campos {fields}"
        )
        return self._handle_rpc(
            lambda: self.models.execute_kw(
                self.db,
                self.uid,
                self.api_key,
                model,
                "search_read",
                [domain],
                {"fields": fields or []},
            )
        )

    def update(self, model, ids, data):
        logger.debug(f"Actualizando {model} con IDs {ids}: {data}")
        return self._handle_rpc(
            lambda: self.models.execute_kw(
                self.db, self.uid, self.api_key, model, "write", [ids, data]
            )
        )

    def delete(self, model, ids):
        logger.debug(f"Eliminando de {model} los IDs {ids}")
        return self._handle_rpc(
            lambda: self.models.execute_kw(
                self.db, self.uid, self.api_key, model, "unlink", [ids]
            )
        )

    def fields_get(self, model, attributes=None):
        logger.debug(f"Obteniendo campos de {model} con atributos {attributes}")
        return self._handle_rpc(
            lambda: self.models.execute_kw(
                self.db,
                self.uid,
                self.api_key,
                model,
                "fields_get",
                [],
                {"attributes": attributes or ["string", "help", "type"]},
            )
        )
