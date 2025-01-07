import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR: Path = Path(__file__).parent.parent.resolve()


class DotEnv(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_DIR, ".env"), env_file_encoding="utf-8", extra="allow"
    )

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


_ = DotEnv()
