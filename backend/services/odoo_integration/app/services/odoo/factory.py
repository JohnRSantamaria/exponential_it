from app.services.odoo.client import OdooClient


class OdooCompanyFactory:
    def __init__(self):
        self._companies = {}

    def register_company(self, name, url, db, username, api_key):
        company = OdooClient(url, db, username, api_key)
        self._companies[name] = company

    def get_company(self, name):
        return self._companies.get(name)

    def list_companies(self):
        return list(self._companies.keys())
