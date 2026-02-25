"""Prometheus metrics for MCP tool calls.

HTTP request metrics are handled automatically by Litestar's PrometheusConfig middleware.
This module only defines MCP-specific tool call metrics.
"""

from prometheus_client import Counter, Gauge, Histogram

# Counter — incremented on each MCP tool call
tool_calls_total = Counter(
    "mcp_tool_calls_total",
    "Total MCP tool calls",
    ["tool_name", "service_name", "status"],
)

# Histogram — observe latency on each MCP tool call
tool_call_duration = Histogram(
    "mcp_tool_call_duration_seconds",
    "Duration of MCP tool calls in seconds",
    ["tool_name", "service_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


# Gauges — set periodically by the health runner / metrics endpoint
services_total = Gauge(
    "mcp_services_total",
    "Total number of configured services",
)

services_healthy = Gauge(
    "mcp_services_healthy",
    "Number of healthy services",
)

tools_enabled = Gauge(
    "mcp_tools_enabled",
    "Number of currently enabled MCP tools",
)


def record_tool_call(
    tool_name: str,
    service_name: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record metrics for a completed tool call."""
    tool_calls_total.labels(
        tool_name=tool_name,
        service_name=service_name,
        status=status,
    ).inc()
    tool_call_duration.labels(
        tool_name=tool_name,
        service_name=service_name,
    ).observe(duration_seconds)
