from typing import List
from fastapi import APIRouter, Body

from app.core.logger import configure_logging
from app.services.odoo.process import odoo_process
from app.services.zoho.schemas.chart_of_accounts_response import ZohoAccount

# Logger
logger = configure_logging()

router = APIRouter()


@router.post("/")
async def entry():
    """ """
    return odoo_process()
