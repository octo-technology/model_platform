from abc import ABC, abstractmethod


class ConfigHandler(ABC):

    @abstractmethod
    def get_var_env(self):
        pass