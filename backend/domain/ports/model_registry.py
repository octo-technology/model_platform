"""Model Registry Port module.

This module defines the abstract base class for the Model Registry port.
"""

from abc import ABC, abstractmethod


class ModelRegistry(ABC):
    """Abstract base class for the Model Registry port."""

    @abstractmethod
    def list_all_models(self) -> list[dict[str, str | int]]:
        """List all registered models in the model registry."""
        pass

    @abstractmethod
    def list_model_versions(self, model_name: str) -> list[dict[str, str | int]]:
        """List all versions of a registered model in the model registry."""
        pass
