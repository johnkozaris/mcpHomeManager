## Dashboard

The dashboard is the main landing page after logging in to MCP Home Manager. It provides an at-a-glance overview of your connected services and recent activity.

### What the Dashboard Shows

**Service health overview** — A summary of all connected services and their current health status:

| Status | Indicator | Meaning |
|--------|-----------|---------|
| Healthy | Green | Service responded successfully to the last health check |
| Unhealthy | Red | Service failed to respond or returned an error |
| Unknown | Gray | Service has not been checked yet |

**Recent activity** — A feed of recent MCP tool calls across all services. Each entry shows the tool name, timestamp, which user or API key triggered it, the target service, and whether the call succeeded or failed.

**Onboarding guidance** — If you have not yet connected any services, the dashboard shows helpful prompts to guide you through adding your first service and configuring an AI agent.

### Health Monitoring

Services are checked periodically in the background (default: every 60 seconds, configurable via `HEALTH_CHECK_INTERVAL_SECONDS`). You can also trigger a manual health check from the service detail page.

Health status changes are reflected on the dashboard in real time when viewing the page.

### Related

- [Connecting Services](connecting-services) — Add new services
- [Self-MCP](self-mcp) — Access dashboard data through your AI agent
