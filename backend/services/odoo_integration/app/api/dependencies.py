# app\api\dependencies.py
import odoorpc
from app.core.settings import settings


def get_odoo_client() -> odoorpc.ODOO:
    try:
        odoo = odoorpc.ODOO(
            settings.ODOO_HOST, port=settings.ODOO_PORT, protocol="jsonrpc+ssl"
        )
        odoo.login(settings.ODOO_DB, settings.ODOO_USER, settings.ODOO_PASSWORD)
        return odoo
    except Exception as e:
        raise ConnectionError(f"Error al conectar con Odoo: {e}")
