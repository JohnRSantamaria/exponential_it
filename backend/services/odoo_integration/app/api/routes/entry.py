from fastapi import APIRouter

from app.services.odoo.process import odoo_process
from app.core.logging import logger

router = APIRouter()


@router.post("/")
async def entry():
    """ """
    logger.debug("Inicia proceso en Odoo.")

    return odoo_process()
