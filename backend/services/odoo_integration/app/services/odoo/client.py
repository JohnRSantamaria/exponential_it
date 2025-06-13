import xmlrpc.client


class OdooClient:
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self.uid = self._authenticate()
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    def _authenticate(self):
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        uid = common.authenticate(self.db, self.username, self.api_key, {})
        if not uid:
            raise Exception("Autenticación fallida con Odoo")
        return uid

    def create(self, model, data):
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "create", [data]
        )

    def read(self, model, domain, fields=None):
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.api_key,
            model,
            "search_read",
            [domain],
            {"fields": fields or []},
        )

    def update(self, model, ids, data):
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "write", [ids, data]
        )

    def delete(self, model, ids):
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "unlink", [ids]
        )
