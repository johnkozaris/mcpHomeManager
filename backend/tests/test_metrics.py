"""Tests for MCP tool call Prometheus metrics."""

from prometheus_client import REGISTRY

from infrastructure.metrics import record_tool_call


class TestMetrics:
    def test_record_tool_call_increments_counter(self) -> None:
        before = (
            REGISTRY.get_sample_value(
                "mcp_tool_calls_total",
                {"tool_name": "test_tool", "service_name": "test_svc", "status": "success"},
            )
            or 0
        )

        record_tool_call("test_tool", "test_svc", "success", 0.123)

        after = REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool_name": "test_tool", "service_name": "test_svc", "status": "success"},
        )
        assert after == before + 1

    def test_record_tool_call_observes_histogram(self) -> None:
        before_count = (
            REGISTRY.get_sample_value(
                "mcp_tool_call_duration_seconds_count",
                {"tool_name": "hist_tool", "service_name": "hist_svc"},
            )
            or 0
        )

        record_tool_call("hist_tool", "hist_svc", "success", 0.5)

        after_count = REGISTRY.get_sample_value(
            "mcp_tool_call_duration_seconds_count",
            {"tool_name": "hist_tool", "service_name": "hist_svc"},
        )
        assert after_count == before_count + 1

    def test_record_error_status(self) -> None:
        record_tool_call("err_tool", "err_svc", "error", 1.0)
        val = REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool_name": "err_tool", "service_name": "err_svc", "status": "error"},
        )
        assert val is not None
        assert val >= 1
