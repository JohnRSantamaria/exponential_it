from app.services.odoo.factory import OdooCompanyFactory
from app.core.settings import settings
from app.services.odoo.operations import get_or_create_address, get_or_create_supplier
from app.services.odoo.schemas.partnet_address import AddressCreateSchema
from app.services.odoo.schemas.supplier import SupplierCreateSchema
from app.services.odoo.schemas.enums import CompanyTypeEnum, AddressTypeEnum

from app.core.logging import logger


def odoo_process():
    """
    El término "partner" (socio) se refiere a cualquier entidad con la que tu empresa interactúe.
    El término "company" (empresa) representa tu propia compañía.
    """
    factory = OdooCompanyFactory()
    logger.info("Creando company")
    factory.register_company(
        name="company1",
        url="https://exptest.gest.ozonomultimedia.com",
        db="odooexptest",
        username="jhon.rincon@exponentialit.net",
        api_key=settings.API_KEY_ODOO,
    )
    logger.debug("Creando creada")
    company = factory.get_company("company1")

    # 👤 Crear proveedor (partner)
    supplier_data = SupplierCreateSchema(
        name="Alvifusta",
        vat="B96382718",
        email="alvifusta@alvifusta.com",
        phone="962239022",
        company_type=CompanyTypeEnum.company,
    )
    partner_id = get_or_create_supplier(company, supplier_data)

    # 🏠 Crear dirección asociada
    address_data = AddressCreateSchema(
        partner_id=partner_id,
        address_name="Bodega Central",
        street="Calle 45A #12-34",
        city="Valencia",
        address_type=AddressTypeEnum.invoice,
        country_id=68,
    )
    address_id = get_or_create_address(company, address_data)

    return {"address_id": address_id}
