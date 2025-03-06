import os

from model_platform.domain.ports.config_handler import ConfigHandler


class ConfigOsAdapter(ConfigHandler):

    def get_var_env(self, var_env_name: str):
        return os.environ[var_env_name]