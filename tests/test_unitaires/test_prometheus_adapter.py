"""Unit tests for Prometheus adapter.

Tests the PrometheusAdapter implementation with mocked HTTP responses.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.infrastructure.prometheus_adapter import PrometheusAdapter


@pytest.mark.asyncio
async def test_get_model_metrics_success():
    """Test successful metrics retrieval for a single model."""
    adapter = PrometheusAdapter()

    # Mock the _execute_query method
    with patch.object(adapter, "_execute_query", new_callable=AsyncMock) as mock_query:
        # Return values: success_rate, total_calls, total_errors
        mock_query.side_effect = [95.0, 45000, 2250]

        result = await adapter.get_model_metrics("credit-v2-prod", "7d")

        assert result is not None
        assert result["success_rate"] == 95.0
        assert result["error_rate"] == 5.0
        assert result["total_calls"] == 45000
        assert result["total_errors"] == 2250

        # Verify 3 queries were made (success_rate, calls, errors)
        assert mock_query.call_count == 3


@pytest.mark.asyncio
async def test_get_model_metrics_not_found():
    """Test when model has no metrics in Prometheus."""
    adapter = PrometheusAdapter()

    with patch.object(adapter, "_execute_query", new_callable=AsyncMock) as mock_query:
        # First query returns None (no data)
        mock_query.side_effect = [None, None, None]

        result = await adapter.get_model_metrics("unknown-model", "7d")

        assert result is None


@pytest.mark.asyncio
async def test_get_model_metrics_zero_calls():
    """Test model with zero API calls."""
    adapter = PrometheusAdapter()

    with patch.object(adapter, "_execute_query", new_callable=AsyncMock) as mock_query:
        # Model with high success rate but zero calls
        mock_query.side_effect = [100.0, 0, 0]

        result = await adapter.get_model_metrics("idle-model", "7d")

        assert result is not None
        assert result["total_calls"] == 0
        assert result["total_errors"] == 0


@pytest.mark.asyncio
async def test_period_to_duration():
    """Test period name to Prometheus duration conversion."""
    adapter = PrometheusAdapter()

    assert adapter._period_to_duration("1d") == "1d"
    assert adapter._period_to_duration("7d") == "7d"
    assert adapter._period_to_duration("30d") == "30d"
    assert adapter._period_to_duration("90d") == "90d"
    assert adapter._period_to_duration("invalid") == "7d"  # Default


@pytest.mark.asyncio
async def test_execute_query_success():
    """Test PromQL query execution with successful response."""
    adapter = PrometheusAdapter()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {"result": [{"value": [1234567890, "95.5"]}]},
    }

    with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        result = await adapter._execute_query("test_query")

        assert result == 95.5


@pytest.mark.asyncio
async def test_execute_query_no_data():
    """Test PromQL query with no results."""
    adapter = PrometheusAdapter()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "success",
        "data": {"result": []},
    }

    with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        result = await adapter._execute_query("test_query")

        assert result is None


@pytest.mark.asyncio
async def test_get_fleet_metrics():
    """Test fleet metrics aggregation across multiple models."""
    adapter = PrometheusAdapter()

    # Mock the model metrics retrieval
    with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
        # Mock label values response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": ["credit-v2", "fraud-detect-v1", "risk-model-v3"],
        }
        mock_get.return_value = mock_response

        # Manually set up return values
        with patch.object(adapter, "get_model_metrics", new_callable=AsyncMock) as mock_metrics:
            mock_metrics.side_effect = [
                {
                    "success_rate": 95.0,
                    "error_rate": 5.0,
                    "total_calls": 10000,
                    "total_errors": 500,
                },
                {
                    "success_rate": 98.0,
                    "error_rate": 2.0,
                    "total_calls": 5000,
                    "total_errors": 100,
                },
                {
                    "success_rate": 92.0,
                    "error_rate": 8.0,
                    "total_calls": 3000,
                    "total_errors": 240,
                },
            ]

            result = await adapter.get_fleet_metrics(None, "7d")

            assert len(result) == 3
            assert result[0]["success_rate"] == 95.0
            assert result[2]["error_rate"] == 8.0
