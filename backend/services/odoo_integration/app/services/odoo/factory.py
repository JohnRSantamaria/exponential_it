from app.services.odoo.client import OdooClient


class OdooClientFactory:
    def __init__(self):
        self._clients = {}

    def register_client(self, name, url, db, username, api_key):
        client = OdooClient(url, db, username, api_key)
        self._clients[name] = client

    def get_client(self, name):
        return self._clients.get(name)

    def list_clients(self):
        return list(self._clients.keys())
