"""Model Registry Port module.

This module defines the abstract base class for the Model Registry port.

In MLflow 3.x, models are first-class entities (LoggedModel) decoupled from runs.
The port exposes both:
- Registered Model methods (for promotion/versioning via aliases)
- LoggedModel methods (for governance: metrics, params, tags, signature, flavors)
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
        """List all versions of a registered model.

        Each entry includes at least: name, version, creation_timestamp, run_id, model_id.
        model_id points to the underlying LoggedModel (MLflow 3.x).
        """
        pass

    @abstractmethod
    def get_model_card(self, model_name: str, version: str) -> str | None:
        """Return the content of model_card.md for the given model version, or None if absent."""
        pass

    @abstractmethod
    def get_logged_model(self, model_name: str, version: str) -> dict:
        """Return the LoggedModel attached to a registered model version.

        Returns a dict with:
            model_id, name, creation_timestamp, source_run_id,
            tags (dict), params (dict), metrics (dict),
            flavors (list[str]), signature (dict | None), model_uri (str)
        """
        pass

    @abstractmethod
    def get_model_governance_information(self, model_name: str, version: str) -> dict:
        """Return governance info for a model version, sourced from LoggedModel + source run.

        Backward-compatible shape used by use cases:
            {
                "model_name": str,
                "version": str,
                "model_id": str,
                "run_id": str | None,
                "creation_timestamp": int,
                "tags": dict,         # merged: run tags + model tags (model wins)
                "params": dict,       # model params (run params as fallback)
                "metrics": dict,      # model metrics (run metrics as fallback)
                "flavors": list[str],
                "signature": dict | None,
                "model_uri": str,
            }
        """
        pass

    @abstractmethod
    def log_model(self, **kwargs) -> None:
        """Log a pyfunc model. In MLflow 3.x the parameter is `name=` (not `artifact_path=`)."""
        pass
