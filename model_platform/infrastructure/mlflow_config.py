"""MLFlow configuration settings module.

This module defines the settings for configuring MLFlow, including environment variables.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from model_platform.config import PROJECT_DIR


class MLFlowSettings(BaseSettings):
    """Settings for configuring MLFlow.

    Attributes
    ----------
    mlflow_s3_endpoint_url : str
        The S3 endpoint URL for MLFlow.
    aws_access_key_id : str
        The AWS access key ID.
    aws_secret_access_key : str
        The AWS secret access key.
    mlflow_tracking_uri : str
        The tracking URI for MLFlow.
    """

    mlflow_s3_endpoint_url: Optional[str]
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    mlflow_tracking_uri: str

    model_config = SettingsConfigDict(env_file=os.path.join(PROJECT_DIR, ".env"), env_file_encoding="utf-8")

    def __init__(self, **data):
        """Initialize the MLFlowSettings instance and set environment variables.

        Parameters
        ----------
        **data : dict
            The data to initialize the settings.
        """
        super().__init__(**data)
        for key, value in self.model_dump().items():
            os.environ[key.upper()] = str(value)


settings = MLFlowSettings()

if __name__ == "__main__":
    settings = MLFlowSettings()
    print("Variables exportées :", os.environ["MLFLOW_TRACKING_URI"])
