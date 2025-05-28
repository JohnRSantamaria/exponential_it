from odoorpc import ODOO
from fastapi import APIRouter, Depends

from app.api.dependencies import get_odoo_client
from app.core.types import CustomAppException
from app.services.odoo.odoo_partner_service import (
    create_draft_invoice,
    create_partner,
    create_supplier,
    get_all_partners,
    get_all_suppliers,
)

router = APIRouter(
    prefix="/odoo",
)


@router.get("/health")
async def health_check():
    """
    Endpoint de verificación de salud para Odoo.
    Retorna un mensaje simple indicando que el servicio está activo.
    """
    data = 0 / 0
    raise CustomAppException(
        status_code=503,
        message="Odoo service is currently unavailable",
    )


@router.get("/version")
async def get_version():
    """
    Endpoint para obtener la versión de Odoo.
    Retorna un mensaje con la versión del servicio Odoo.
    """
    return {"version": "Odoo 16.0", "status": "Odoo service is running"}


@router.get("/info")
async def get_info():
    """
    Endpoint para obtener información del servicio Odoo.
    Retorna un mensaje con información básica del servicio Odoo.
    """
    return {
        "service": "Odoo",
        "version": "16.0",
        "description": "Odoo is an open-source suite of business applications.",
        "status": "Odoo service is running",
    }


# ---------------------
# Clientes
# ---------------------


@router.get("/partners")
def list_partners(odoo: ODOO = Depends(get_odoo_client)):
    return get_all_partners(odoo)


@router.post("/partners", response_model=dict, status_code=201)
def create_new_partner(data, odoo: ODOO = Depends(get_odoo_client)):
    return create_partner(data, odoo)


# ---------------------
# Proveedores
# ---------------------


@router.get("/suppliers")
def list_suppliers(odoo: ODOO = Depends(get_odoo_client)):
    return get_all_suppliers(odoo)


@router.post("/suppliers", response_model=dict, status_code=201)
def create_new_supplier(data, odoo: ODOO = Depends(get_odoo_client)):
    return create_supplier(data, odoo)


# ---------------------
# Facturas
# ---------------------


@router.post("/invoices", response_model=dict, status_code=201)
def create_invoice(data, odoo: ODOO = Depends(get_odoo_client)):
    return create_draft_invoice(data, odoo)
