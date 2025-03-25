from backend.infrastructure.config_os_adapter import ConfigOsAdapter
from backend.utils import Singleton


class Config(metaclass=Singleton):

    def __init__(self, env="local"):
        if env == "prod":
            config_adapter = ConfigOsAdapter()
        else:
            config_adapter = ConfigOsAdapter()
        self.jwt_secret = config_adapter.get_var_env("JWT_SECRET")
        self.db_path = config_adapter.get_var_env("PROJECTS_DB_PATH")
        self.jwt_algorithm = "HS256"
        self.jwt_access_token_expiration_time = 600
