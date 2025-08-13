import re
import difflib
import base64

from datetime import datetime

from fastapi import HTTPException, UploadFile, status

from app.core.logging import logger
from app.services.odoo.client import AsyncOdooClient
from app.services.odoo.exceptions import OdooCallException
from app.services.odoo.schemas.invoice import InvoiceCreateSchemaV18
from app.services.odoo.utils.cleanner import clean_enum_payload, parse_to_date

from exponential_core.exceptions import TaxIdNotFoundError
from exponential_core.odoo import (
    TaxUseEnum,
    AddressCreateSchema,
    ProductCreateSchema,
    SupplierCreateSchema,
)


def normalize_vat_for_search(vat: str) -> str:
    return re.sub(r"[^0-9]", "", vat.strip().upper())  # solo números


async def get_or_create_supplier(
    company: AsyncOdooClient, supplier_data: SupplierCreateSchema
):
    search_vat = normalize_vat_for_search(supplier_data.vat)

    existing = await company.read(
        "res.partner",
        [["vat", "ilike", supplier_data.vat]],
        fields=["id", "vat", "name"],
    )

    for partner in existing:
        vat_db = partner["vat"] or ""
        vat_db_clean = normalize_vat_for_search(vat_db)
        if vat_db_clean.startswith(search_vat) or search_vat.startswith(vat_db_clean):
            logger.debug(
                f"Supplier encontrado por VAT normalizado: {partner['id']} {partner.get("name","")}"
            )
            return partner["id"]

    # 🔹 Si no lo encontró, lo crea

    logger.debug("Creando Supplier")
    payload = clean_enum_payload(supplier_data.as_odoo_payload())
    return await company.create("res.partner", payload)


import difflib


async def get_or_create_address(
    company: AsyncOdooClient,
    address_data: AddressCreateSchema,
    similarity_threshold=0.8,
):
    # Buscar dirección invoice exacta del partner
    domain_invoice = [
        ["parent_id", "=", address_data.partner_id],
        ["type", "=", "invoice"],
    ]
    existing_invoice = await company.read(
        "res.partner", domain_invoice, fields=["id", "street", "city"]
    )
    if existing_invoice:
        logger.debug(
            f"Usando dirección invoice existente del partner {address_data.partner_id}: {existing_invoice[0]['id']}"
        )
        return existing_invoice[0]["id"]

    # Buscar candidatos
    domain_flexible = [
        ["type", "=", "invoice"],
        ["street", "ilike", address_data.street.split()[0]],
        ["city", "ilike", address_data.city],
    ]
    if address_data.country_id:
        domain_flexible.append(["country_id", "=", address_data.country_id])
    if address_data.zip:
        domain_flexible.append(["zip", "=", address_data.zip])

    candidates = await company.read(
        "res.partner", domain_flexible, fields=["id", "street", "city", "zip", "name"]
    )

    # Calcular similitud fuzzy
    def similarity_ratio(text1, text2):
        if not text1 or not text2:
            return 0.0
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    # Evalua cada candidato y guardar el mejor
    best_candidate = None
    best_score = 0.0

    for candidate in candidates:
        street_score = similarity_ratio(
            candidate.get("street", ""), address_data.street
        )
        city_score = similarity_ratio(candidate.get("city", ""), address_data.city)
        name_score = similarity_ratio(
            candidate.get("name", ""), address_data.address_name
        )

        # Peso total: 50% street, 30% city, 20% name
        total_score = (street_score * 0.5) + (city_score * 0.3) + (name_score * 0.2)

        # Log de cada candidato
        logger.debug(
            f"[CHECK] ID={candidate['id']} | Street='{candidate.get('street')}' "
            f"| City='{candidate.get('city')}' | Name='{candidate.get('name')}' "
            f"-> Score={total_score:.2f} (street={street_score:.2f}, city={city_score:.2f}, name={name_score:.2f})"
        )

        if total_score > best_score:
            best_score = total_score
            best_candidate = candidate

    # Si hay un candidato suficientemente similar, usarlo
    if best_candidate and best_score >= similarity_threshold:
        logger.debug(
            f"✅ Usando dirección más similar encontrada (score={best_score:.2f}): "
            f"{best_candidate['id']} ({best_candidate['street']}, {best_candidate['city']})"
        )
        return best_candidate["id"]

    # Si no hay coincidencias fuertes, crear una nueva dirección
    logger.debug(f"➕ Creando nueva dirección para partner {address_data.partner_id}")
    payload = clean_enum_payload(address_data.as_odoo_payload())
    return await company.create("res.partner", payload)


async def get_tax_ids(company: AsyncOdooClient) -> list[dict]:

    logger.debug(
        f"Buscando las taxes asociadas a la compañia con id : { company.company_id}"
    )

    taxes = await company.read(
        "account.tax",
        [
            ["type_tax_use", "=", "sale"],
            ["active", "=", True],
            ["company_id.id", "=", company.company_id],
        ],
        fields=["id", "name", "amount", "type_tax_use", "active"],
    )

    logger.debug("Taxes encontradas".center(50, "*"))
    logger.debug(f"total : {len(taxes)}")

    return taxes


async def get_tax_id_by_amount(
    company: AsyncOdooClient,
    amount: float,
    tax_type: TaxUseEnum,
) -> int:
    taxes = await company.read(
        "account.tax",
        [["type_tax_use", "=", tax_type.value]],
        fields=["id", "amount"],
    )

    candidates = [round(t["amount"], 2) for t in taxes]

    for tax in taxes:
        if round(tax["amount"], 2) == round(amount, 2):
            return tax["id"]

    raise TaxIdNotFoundError(invoice_number="", candidates=candidates)


async def get_or_create_product(
    company: AsyncOdooClient, product_data: ProductCreateSchema
):
    domain = [["name", "=", product_data.name]]
    if product_data.default_code:
        domain.append(["default_code", "=", product_data.default_code])

    existing = await company.read("product.product", domain, fields=["id"])
    if existing:
        logger.debug(f"Producto ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando producto")
    payload = clean_enum_payload(product_data.model_dump(exclude_none=True))
    return await company.create("product.product", payload)


async def get_or_create_invoice(
    company: AsyncOdooClient, invoice_data: InvoiceCreateSchemaV18
) -> int:
    """
    Crea o devuelve una factura de proveedor (move_type='in_invoice') si ya existe.
    Se considera duplicada si coincide `ref` (número de factura) y `partner_id`.
    """

    domain = [
        ["move_type", "=", "in_invoice"],
        ["ref", "=", invoice_data.ref],  # Número de factura del proveedor
        ["partner_id", "=", invoice_data.partner_id],
    ]

    existing = await company.read("account.move", domain, fields=["id"])
    if existing:
        logger.debug(f"Factura ya existente: {existing[0]["id"]}")
        return existing[0]["id"]

    logger.debug(f"Creando factura")
    payload = invoice_data.as_odoo_payload()

    if "invoice_date" in payload and isinstance(payload["invoice_date"], datetime):
        payload["invoice_date"] = parse_to_date(payload.get("invoice_date"))
    if "date" in payload and isinstance(payload["date"], datetime):
        payload["date"] = parse_to_date(payload.get("date"))

    invoice_id = await company.create("account.move", payload)

    logger.info(f"Factura creada: {invoice_id}")

    # 4️⃣ Publicar mensaje en el chatter
    await company.call(
        "account.move",
        "message_post",
        [[invoice_id]],
        {
            "body": "<p>🤖 Esta factura fue creada automáticamente con asistencia de AI y debe ser verificada.</p>"
        },
    )

    return invoice_id


async def attach_file_to_invoice(
    company: AsyncOdooClient, invoice_id: str, file: UploadFile
):
    """
    Adjunta un archivo PDF o imagen a la factura especificada en Odoo.
    """
    # 1️⃣ Leer el archivo y codificar en Base64
    file_content = await file.read()
    encoded_file = base64.b64encode(file_content).decode("utf-8")
    file_name = file.filename

    # 2️⃣ Crear payload con contenido codificado
    attachment_payload = {
        "name": file_name,
        "type": "binary",
        "datas": encoded_file,  # 🔹 AHORA es Base64 string, no bytes
        "res_model": "account.move",
        "res_id": int(invoice_id),
        "mimetype": (
            "application/pdf" if file_name.lower().endswith(".pdf") else "image/png"
        ),
    }

    # 3️⃣ Crear el attachment en Odoo
    attachment_id = await company.create("ir.attachment", attachment_payload)

    logger.debug(
        f"📎 Archivo '{file_name}' adjuntado a la factura ID={invoice_id} (Attachment ID={attachment_id})"
    )
    return attachment_id


async def get_model_fields(company: AsyncOdooClient, model: str) -> dict:
    """
    Retorna todos los campos disponibles de un modelo Odoo, incluyendo tipo y etiqueta.

    - model: nombre del modelo Odoo que se desea consultar. Ejemplos comunes:
        - 'res.partner': Representa contactos, proveedores y clientes en Odoo.
        - 'account.tax': Representa los diferentes tipos de impuestos configurados en Odoo.
        - 'product.product': Representa productos (SKU) individuales disponibles para vender o comprar.
        - 'account.move': Representa facturas, asientos contables y otros movimientos financieros.

    Retorna:
        diccionario {nombre_campo: {'type': ..., 'string': ...}}
        Por ejemplo: {'id': {'type': 'integer', 'string': 'ID'}, ...}
    """
    fields = await company.fields_get(model)
    return {
        name: {
            "string": meta["string"],
            "type": meta["type"],
            "help": meta.get("help"),
        }
        for name, meta in fields.items()
    }


async def get_required_fields(company: AsyncOdooClient, model: str) -> dict:
    """
    Retorna un diccionario con la metadata de los campos obligatorios de un modelo Odoo,
    incluyendo tipo y etiqueta.

    - model: nombre del modelo Odoo que se desea consultar. Ejemplos comunes:
        - 'res.partner': Representa contactos, proveedores y clientes en Odoo.
        - 'account.tax': Representa los diferentes tipos de impuestos configurados en Odoo.
        - 'product.product': Representa productos (SKU) individuales disponibles para vender o comprar.
        - 'account.move': Representa facturas, asientos contables y otros movimientos financieros.

    Retorna:
        diccionario {nombre_campo: {'type': ..., 'string': ...}} solo para los campos obligatorios.
        Por ejemplo: {'name': {'type': 'char', 'string': 'Nombre'}, ...}
    """
    fields = await company.fields_get(model)
    return {
        name: {
            "string": meta["string"],
            "type": meta["type"],
            "help": meta.get("help"),
        }
        for name, meta in fields.items()
        if meta.get("required")
    }


async def get_companies(
    company: AsyncOdooClient, name_filter: str | None = None
) -> list[dict]:
    """
    Obtiene todas las compañías asociadas al cliente Odoo.
    Si se pasa name_filter, filtra las compañías cuyo nombre contenga ese texto.
    """
    domain = []
    if name_filter:
        domain.append(["name", "ilike", name_filter])

    companies = await company.read(
        model="res.company",
        domain=domain,
        fields=["id", "name"],  # ✅ Retornar solo campos necesarios
    )
    return companies


async def get_invoice_total(company: AsyncOdooClient, invoice_id: int):

    recs = await company.read(
        "account.move",
        [["id", "=", invoice_id]],
        fields=[
            "id",
            "amount_total",
            "currency_id",
            "name",
            "ref",
            "move_type",
            "state",
        ],
    )
    if not recs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {invoice_id} no encontrada",
        )

    rec = recs[0]
    # currency_id es un m2o: [id, 'Name'] -> opcionalmente puedes devolver el nombre
    currency = (
        rec.get("currency_id", [None, None])[1] if rec.get("currency_id") else None
    )

    return {
        "invoice_id": rec["id"],
        "amount_total": rec["amount_total"],
        "currency": currency,
        "name": rec.get("name"),
        "ref": rec.get("ref"),
        "move_type": rec.get("move_type"),
        "state": rec.get("state"),
    }


async def delete_invoice_by_invoice_id(
    invoice_id: int,
    company: AsyncOdooClient,
    force: bool = True,
):
    # Helper para verificar existencia rápida
    recs = await company.read(
        "account.move",
        [["id", "=", invoice_id]],
        fields=["id", "state", "move_type"],
    )
    if not recs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Factura {invoice_id} no encontrada",
        )

    try:

        await company.delete("account.move", [invoice_id])
        return {"deleted": True, "invoice_id": invoice_id, "forced": False}
    except OdooCallException as e:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se pudo eliminar la factura {invoice_id}: {e}",
            ) from e

        try:
            await company.call("account.move", "button_cancel", [[invoice_id]])
            await company.delete("account.move", [invoice_id])
            return {"deleted": True, "invoice_id": invoice_id, "forced": True}
        except Exception as e2:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se pudo eliminar la factura {invoice_id} incluso tras cancelar: {e2}",
            ) from e2
