"""MLFlow configuration settings module.

This module defines the settings for configuring MLFlow, including environment variables.
"""

import sys

import mlflow
from loguru import logger
from mlflow import MlflowException


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

        Tries to create an instance of MlflowClient and logs the result.
        If initialization fails, logs the error and sets the client to None.
        """
        try:
            logger.info(f"Initializing MLflow client with tracking URI: {self.tracking_uri}")
            self.client = mlflow.MlflowClient(tracking_uri=self.tracking_uri)
            self._check_connection()
            logger.info("MLflow client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize MLflow client: {e}")
            self.client = None

    def _check_connection(self):
        try:
            _ = self.client.search_experiments()
        except MlflowException as e:
            self.client = None
            logger.error(f"Failed to connect to MLflow server: {e}")
            sys.exit(1)

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
