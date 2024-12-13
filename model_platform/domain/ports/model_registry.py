"""Model Registry Port module.

This module defines the abstract base class for the Model Registry port.
"""

from abc import ABC, abstractmethod


class ModelRegistry(ABC):
    """Abstract base class for the Model Registry port."""

    def __init__(self):
        """Initialize the ModelRegistry instance."""
        pass

    @abstractmethod
    def list_all_models(self):
        """List all registered models in the model registry."""
        pass
