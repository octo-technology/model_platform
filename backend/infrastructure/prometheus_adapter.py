"""Prometheus adapter for metrics retrieval.

Implements MetricsHandler to retrieve real-time metrics from Prometheus
time-series database. Handles connection pooling, query building, and
error recovery.
"""

import os
from typing import Optional

import httpx
from loguru import logger

from backend.domain.ports.metrics_handler import MetricsHandler, MetricsResult


class PrometheusAdapter(MetricsHandler):
    """Adapter for querying Prometheus metrics.

    Translates PromQL queries into metrics accessible by use cases.
    Handles connection pooling, retries, and query timeout management.

    Parameters
    ----------
    prometheus_url : str
        Prometheus HTTP API endpoint URL. Defaults to env var
        PROMETHEUS_URL or K8s service DNS name.
    query_timeout : int
        Query timeout in seconds (default: 30)
    """

    def __init__(
        self,
        prometheus_url: Optional[str] = None,
        query_timeout: int = 30,
    ):
        # Use provided URL, env var, or K8s service DNS
        if prometheus_url is None:
            prometheus_url = os.getenv(
                "PROMETHEUS_URL",
                "http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090",
            )
        self.prometheus_url = prometheus_url
        self.query_timeout = query_timeout
        self.client = httpx.AsyncClient(timeout=self.query_timeout)
        logger.info(f"PrometheusAdapter initialized: {prometheus_url}")

    def _period_to_duration(self, period: str) -> str:
        """Convert period name to Prometheus duration format.

        Parameters
        ----------
        period : str
            Period name: '1d', '7d', '30d', '90d'

        Returns
        -------
        str
            Prometheus duration format: '1d', '7d', etc.
        """
        mapping = {
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "6h": "6h",
            "1d": "1d",
            "7d": "7d",
            "30d": "30d",
        }
        result = mapping.get(period, "7d")
        logger.debug(f"Period {period} maps to duration {result}")
        return result

    async def _execute_query(self, query: str) -> Optional[float]:
        """Execute PromQL query and extract scalar value.

        Parameters
        ----------
        query : str
            PromQL query string

        Returns
        -------
        Optional[float]
            Scalar result or None if query fails / no data

        Raises
        ------
        Exception
            If HTTP request fails or response parsing fails
        """
        try:
            logger.debug(f"Executing PromQL: {query[:100]}...")
            response = await self.client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=self.query_timeout,
            )
            response.raise_for_status()

            data = response.json()

            if data["status"] != "success":
                logger.warning(f"PromQL error: {data.get('error', 'Unknown error')}")
                return None

            # Extract scalar value from response
            if data.get("data", {}).get("result"):
                value = float(data["data"]["result"][0]["value"][1])
                logger.debug(f"Query result: {value}")
                return value

            logger.debug("Query returned no data")
            return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying Prometheus: {e}")
            raise
        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Prometheus response: {e}")
            raise

    async def get_model_metrics(self, model_id: str, period: str = "7d") -> Optional[MetricsResult]:
        """Query metrics for a single deployed model.

        Uses OpenTelemetry http_server_duration_milliseconds_count metric,
        filtered by the Prometheus 'job' label (set to K8s service name)
        and http_target="/predict" to count only prediction requests.

        PromQL Queries Used:
        - total_calls: sum(increase(http_server_duration_milliseconds_count{job=..., http_target="/predict"}[period]))
        - total_errors: sum(increase(http_server_duration_milliseconds_count{
            job=..., http_target="/predict", http_status_code!~"2.."}[period]))

        Parameters
        ----------
        model_id : str
            K8s service / deployment name (matches Prometheus 'job' label)
        period : str
            Time window: '1d', '7d', '30d', '90d'

        Returns
        -------
        Optional[MetricsResult]
            Dictionary with metrics or None if no data found

        Raises
        ------
        Exception
            If Prometheus connection fails or query times out
        """
        try:
            duration = self._period_to_duration(period)
            logger.debug(f"Querying metrics for model_id={model_id}, period={period} " f"(duration={duration})")

            # Total calls to /predict endpoint (all status codes)
            calls_query = (
                f"sum(increase(http_server_duration_milliseconds_count{{"
                f'job="{model_id}",http_target="/predict"}}[{duration}]))'
            )
            total_calls_raw = await self._execute_query(calls_query)

            if total_calls_raw is None:
                logger.warning(f"No metrics data for model {model_id}")
                return None

            total_calls = int(total_calls_raw)

            # Total errors: non-2xx status codes on /predict
            errors_query = (
                f"sum(increase(http_server_duration_milliseconds_count{{"
                f'job="{model_id}",http_target="/predict",'
                f'http_status_code!~"2.."}}[{duration}]))'
            )
            total_errors_raw = await self._execute_query(errors_query)
            # Empty result means no errors
            total_errors = int(total_errors_raw) if total_errors_raw is not None else 0

            # Compute rates
            if total_calls > 0:
                error_rate = round(100.0 * total_errors / total_calls, 2)
            else:
                error_rate = 0.0
            success_rate = round(100.0 - error_rate, 2)

            result: MetricsResult = {
                "success_rate": success_rate,
                "error_rate": error_rate,
                "total_calls": total_calls,
                "total_errors": total_errors,
            }

            logger.info(
                f"Metrics for {model_id}: "
                f"success_rate={result['success_rate']}%, "
                f"total_calls={result['total_calls']}, "
                f"total_errors={result['total_errors']}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to query metrics for model {model_id}: {e}")
            raise

    async def get_fleet_metrics(self, project_name: Optional[str] = None, period: str = "7d") -> list[MetricsResult]:
        """Query metrics for all models in fleet or specific project.

        This aggregates metrics across multiple models by querying
        all models returned from Prometheus label values.

        Parameters
        ----------
        project_name : Optional[str]
            Filter by project, None returns all projects
        period : str
            Time window

        Returns
        -------
        list[MetricsResult]
            List of metrics per model
        """
        try:
            logger.debug(f"Querying fleet metrics: project={project_name}, period={period}")

            # Discover model jobs by finding all 'job' label values that have
            # /predict traffic. The 'job' label is set by Prometheus to the K8s
            # service name, which matches the deployment name (model_id).
            if project_name:
                match_selector = (
                    f"http_server_duration_milliseconds_count{{" f'http_target="/predict",namespace="{project_name}"}}'
                )
            else:
                match_selector = 'http_server_duration_milliseconds_count{http_target="/predict"}'

            response = await self.client.get(
                f"{self.prometheus_url}/api/v1/label/job/values",
                params={"match[]": match_selector},
                timeout=self.query_timeout,
            )
            response.raise_for_status()
            data = response.json()

            if data["status"] != "success":
                logger.warning(f"Failed to list models: {data.get('error')}")
                return []

            model_ids = data.get("data", [])
            logger.info(f"Found {len(model_ids)} models in fleet")

            # Query metrics for each model
            metrics_list = []
            for model_id in model_ids:
                try:
                    result = await self.get_model_metrics(model_id, period)
                    if result:
                        metrics_list.append(result)
                except Exception as e:
                    logger.warning(f"Failed to get metrics for {model_id}: {e}")
                    continue

            logger.info(f"Retrieved metrics for {len(metrics_list)} models")
            return metrics_list

        except Exception as e:
            logger.error(f"Failed to query fleet metrics: {e}")
            raise

    async def close(self):
        """Close HTTP client connection pool.

        Should be called during application shutdown.
        """
        await self.client.aclose()
        logger.info("PrometheusAdapter closed")
