class ProviderConfig:
    def __init__(
        self,
        server_url: str,
        token: str = None,
        user: str = None,
        password: str = None,
    ):

        self.server_url = server_url
        self.token = token
        self.user = user
        self.password = password
