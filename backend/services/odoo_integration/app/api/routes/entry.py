from fastapi import APIRouter

from app.services.odoo.process import odoo_process
from exponential_core.logger.configure import configure_logging

# Logger
logger = configure_logging()

router = APIRouter()


@router.post("/")
async def entry():
    """ """
    logger.info("Inicia proceso en Odoo.")

    return odoo_process()
