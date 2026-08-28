"""MLFlow configuration settings module.

This module defines the settings for configuring MLFlow, including environment variables.
"""

import mlflow
from loguru import logger


class MLflowClientManager:
    """
    Manages the MLflow client initialization and retrieval.

    Attributes
    ----------
    client : MlflowClient or None
        The MLflow client instance.
    """

    def __init__(self, tracking_uri: str):
        """
        Initializes the MLflowClientManager with no client.
        """
        self.client = None
        self.tracking_uri = tracking_uri

    def initialize(self):
        """
        Initializes the MLflow client.

        Raises if the registry does not answer: a client that cannot reach its
        registry must not be cached, and one broken project must not take the
        others down with it.
        """
        logger.info(f"Initializing MLflow client with tracking URI: {self.tracking_uri}")
        self.client = mlflow.MlflowClient(tracking_uri=self.tracking_uri)
        self._check_connection()
        logger.info("MLflow client initialized successfully.")

    def _check_connection(self):
        """Raise if the registry is unreachable, so callers keep it out of the pool."""
        self.client.search_experiments()

    def close(self):
        """
        Closes the MLflow client if it is initialized.

        If the client is not initialized, logs a warning.
        """
        if self.client:
            self.client = None
            logger.info("MLflow client closed.")
        else:
            logger.warning("MLflow client is not initialized.")
