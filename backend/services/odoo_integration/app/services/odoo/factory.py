from app.services.odoo.client import OdooClient


class OdooCompanyFactory:
    def __init__(self):
        self._companies = {}

    def register_company(self, client_vat, url, db, username, api_key):
        company = OdooClient(url, db, username, api_key)
        self._companies[client_vat] = company

    def get_company(self, client_vat):
        return self._companies.get(client_vat)

    def list_companies(self):
        return list(self._companies.keys())
