class   ProviderConfig:
    def __init__(
        self,
        server_url: str,
        token: str = None,
        user: str = None,
        password: str = None,
        api_prefix: str = None,
    ):

        self.server_url = server_url
        self.api_prefix = api_prefix
        self.user = user
        self.token = token
        self.password = password

        self.path = (
            f"{server_url}{api_prefix}" if api_prefix is not None else server_url
        )
