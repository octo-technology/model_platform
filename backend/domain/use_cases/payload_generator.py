# Author: Octo Technology MLOps Tribe
"""Dynamic payload generation from MLflow model feature schemas."""

import concurrent.futures
import random
import tempfile
from dataclasses import dataclass

import mlflow
import mlflow.models
import yaml
from loguru import logger


@dataclass
class FeatureSpec:
    name: str
    dtype: str  # "int64" | "float64"
    range_min: float | None = None
    range_max: float | None = None
    isin_values: list | None = None


class SchemaDiscoverer:
    """Discovers model input schema from MLflow artifacts or model signature.

    Discovery strategy:
    1. Fetch the model signature input names — these are the ground truth for
       which columns the model actually expects (excludes targets).
    2. Download the pandera_schema.yaml artifact for rich metadata (ranges,
       categorical sets).  Filter its columns to only those in the signature
       so that target columns present in the pandera schema are excluded.
    3. If the pandera artifact is missing, fall back to signature-only specs
       (column names, no value ranges).
    """

    TIMEOUT_SECONDS = 15

    def __init__(self, client: mlflow.MlflowClient):
        self._client = client

    def get_feature_specs(self, model_name: str, version: str) -> list[FeatureSpec]:
        try:
            run_id = self._client.get_model_version(model_name, version).run_id
            logger.info(f"Got run_id {run_id} for {model_name} v{version}")
        except Exception as e:
            logger.warning(f"Failed to get run_id for {model_name} v{version}: {type(e).__name__}: {e}")
            return []

        # Ground truth: the columns the model was trained on
        input_names = self._get_signature_input_names(model_name, version)
        logger.info(f"Signature input names for {model_name} v{version}: {input_names}")

        # Rich path: pandera schema with value ranges / categorical sets
        specs = self._try_pandera_schema(run_id)
        if specs is not None:
            if input_names:
                specs = [s for s in specs if s.name in input_names]
            return specs

        # Fallback: signature-only (no value ranges)
        return [FeatureSpec(name=name, dtype="float64") for name in input_names]

    def _get_signature_input_names(self, model_name: str, version: str) -> list[str]:
        """Return ordered list of model input column names from MLflow signature."""
        try:

            def _fetch():
                info = mlflow.models.get_model_info(f"models:/{model_name}/{version}")
                if info.signature and info.signature.inputs:
                    return [col.name for col in info.signature.inputs]
                return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(_fetch).result(timeout=self.TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            logger.warning(f"MLflow signature fetch timeout (>{self.TIMEOUT_SECONDS}s) for {model_name} v{version}")
            return []
        except Exception as e:
            logger.warning(f"Could not get model signature for {model_name} v{version}: {type(e).__name__}: {e}")
            return []

    def _try_pandera_schema(self, run_id: str) -> list[FeatureSpec] | None:
        try:
            with tempfile.TemporaryDirectory() as tmp:

                def _download():
                    return self._client.download_artifacts(run_id, "pandera_schema.yaml", tmp)

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    path = pool.submit(_download).result(timeout=self.TIMEOUT_SECONDS)
                with open(path) as f:
                    data = yaml.safe_load(f)
            logger.info(f"Successfully downloaded pandera_schema.yaml for run {run_id}")
            return self._parse_pandera_yaml(data)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Pandera schema download timeout (>{self.TIMEOUT_SECONDS}s) for run {run_id}")
            return None
        except FileNotFoundError:
            logger.warning(f"pandera_schema.yaml not found for run {run_id}")
            return None
        except Exception as e:
            logger.warning(f"Pandera schema not available for run {run_id}: {type(e).__name__}: {e}")
            return None

    def _parse_pandera_yaml(self, data: dict) -> list[FeatureSpec]:
        specs = []
        for col_name, col_def in data.get("columns", {}).items():
            dtype = col_def.get("dtype", "float64")
            range_min = range_max = None
            isin_values = None
            for check in col_def.get("checks") or []:
                check_name = (check.get("options") or {}).get("check_name")
                if check_name == "in_range":
                    range_min = check.get("min_value")
                    range_max = check.get("max_value")
                elif check_name == "isin":
                    isin_values = check.get("value")
            specs.append(
                FeatureSpec(
                    name=col_name,
                    dtype=dtype,
                    range_min=range_min,
                    range_max=range_max,
                    isin_values=isin_values,
                )
            )
        return specs


class PayloadGenerator:
    """Generates random payloads from a list of FeatureSpec."""

    def generate(self, specs: list[FeatureSpec]) -> dict:
        return {"inputs": {spec.name: self._sample(spec) for spec in specs}}

    def _sample(self, spec: FeatureSpec) -> float:
        if spec.isin_values:
            return float(random.choice(spec.isin_values))
        if "int" in spec.dtype:
            lo = int(spec.range_min) if spec.range_min is not None else 0
            hi = int(spec.range_max) if spec.range_max is not None else 100
            return float(random.randint(lo, hi))
        lo = spec.range_min if spec.range_min is not None else 0.0
        hi = spec.range_max if spec.range_max is not None else 1.0
        return round(random.uniform(lo, hi), 4)


def build_feature_specs(tracking_uri: str, model_name: str, model_version: str) -> list[FeatureSpec]:
    """Return feature specs from MLflow, or [] on any failure.

    K8s deployment names use hyphens (customer-churn-predictor) but MLflow
    registered model names use underscores (customer_churn_predictor).
    This function converts hyphens back to underscores before querying.
    """
    try:
        mlflow_model_name = model_name.replace("-", "_")
        logger.info(f"Starting feature discovery for {mlflow_model_name} v{model_version} from {tracking_uri}")
        mlflow.set_tracking_uri(tracking_uri)
        client = mlflow.MlflowClient(tracking_uri=tracking_uri)
        discoverer = SchemaDiscoverer(client)
        specs = discoverer.get_feature_specs(mlflow_model_name, model_version)
        if specs:
            feature_names = [spec.name for spec in specs]
            logger.info(f"Discovered {len(specs)} features for {model_name} v{model_version}: {feature_names}")
        else:
            logger.info(
                f"No features discovered for {model_name} v{model_version} (will fall back to hardcoded payload)"
            )
        return specs
    except Exception as e:
        logger.warning(f"Feature schema discovery failed for {model_name} v{model_version}: {type(e).__name__}: {e}")
        return []
