## Developer Resources

MCP Home Manager is an open-source project. Contributions, bug reports, and feature requests are welcome.

### Getting Involved

- [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) — Dev environment setup, coding standards, and PR process
- [GitHub Issues](https://github.com/johnkozaris/mcpHomeManager/issues) — Report bugs or request features
- [GitHub Releases](https://github.com/johnkozaris/mcpHomeManager/releases) — Changelog and release notes

### Architecture

```
backend/           Python 3.14, Litestar, FastMCP, SQLAlchemy, aiosqlite/asyncpg
frontend/          React 19, Vite, Tailwind v4, TanStack Query
```

The backend follows **hexagonal architecture** (Ports & Adapters):

- **Domain layer** — Entities (`ServiceConnection`, `ToolDefinition`, `User`), ports (interfaces), and business logic
- **Infrastructure layer** — Service client adapters (one per service type), database persistence (SQLAlchemy), encryption
- **Entrypoints** — Litestar REST API (web UI backend) and MCP server (AI agent endpoint)

#### MCP Server Instructions

The MCP server sends dynamic instructions to connected AI agents so they understand what's available without manual prompting.

`_build_server_instructions()` in `entrypoints/mcp/server.py` generates the instruction string from the current server state. It lists connected services with human-readable labels from a `_type_labels` dict (e.g., `forgejo` → "Git hosting", `paperless` → "document management"). When self-MCP is enabled, the instructions include the supported `service_type` enum values and direct the agent to use management tools. When self-MCP is off, they point the agent to the web UI instead.

Instructions are refreshed after every `sync_tools()` call via `_refresh_instructions()`, which writes directly to `self._mcp._mcp_server.instructions` (FastMCP has no public setter for this).

#### Meta-Tools

Self-MCP management tools are defined in `entrypoints/mcp/meta_tools.py`.

`META_TOOL_NAMES` is a tuple of all meta-tool names, used by the server factory to register or remove them when self-MCP is toggled. `register_meta_tools()` takes the FastMCP instance, session factory, encryption, client factory, and tool registry, then registers all tool handlers.

The full set of meta-tools:

| Tool | Access | Purpose |
|------|--------|---------|
| `mcp_home_list_services` | self-MCP | List services with health and tool counts |
| `mcp_home_add_service` | admin + self-MCP | Connect a new service |
| `mcp_home_update_service` | admin + self-MCP | Update service URL, credentials, or state |
| `mcp_home_delete_service` | admin + self-MCP | Delete a service and its tools |
| `mcp_home_toggle_tool` | admin + self-MCP | Enable/disable a tool |
| `mcp_home_list_tools` | self-MCP | List all tools with status |
| `mcp_home_health` | self-MCP | System health summary |
| `mcp_home_get_logs` | self-MCP | Query audit logs |
| `mcp_home_add_generic_tool` | admin + self-MCP | Define a custom tool on any service |
| `mcp_home_update_generic_tool` | admin + self-MCP | Modify a custom tool definition |
| `mcp_home_delete_generic_tool` | admin + self-MCP | Remove a custom tool |
| `mcp_home_ui_dashboard` | self-MCP | Interactive HTML dashboard |
| `mcp_home_ui_service_control` | self-MCP | Interactive service control panel |
| `mcp_home_ui_config` | self-MCP | Interactive config viewer |

Write operations (add, update, delete, toggle) require admin privileges checked via `_require_admin_user()`. All meta-tools require self-MCP access checked via `_require_self_mcp_access()`, which verifies both the global setting and the per-user flag.

### Service Adapter Structure

Each service integration is a self-contained client in `backend/src/infrastructure/clients/`:

```
base_client.py              Base class with shared HTTP, auth, error handling
homeassistant_client.py     Home Assistant adapter
paperless_client.py         Paperless-ngx adapter
...                         (17 adapters total)
```

Every adapter implements the `IServiceClient` interface:
- `health_check()` — Verify the service is reachable
- `execute_tool(tool_name, arguments)` — Run a named tool
- `get_tool_definitions()` — Return available tools with JSON Schema parameters

Some adapters also implement `IAppProvider` to serve interactive HTML apps via MCP (e.g., Home Assistant entity dashboard, Paperless document search, Forgejo repo browser).

### Key Technologies

| Component | Technology |
|-----------|-----------|
| Web framework | [Litestar](https://litestar.dev/) |
| MCP server | [FastMCP](https://github.com/jlowin/fastmcp) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite (default) or PostgreSQL (via `DATABASE_URL`) |
| Frontend | React 19 + TypeScript + Vite 6 |
| Package management | uv (Python), pnpm (Node) |

### API

The REST API serves the web UI frontend. The OpenAPI schema is not exposed via Swagger UI in production (openapi disabled). Refer to the source code in `backend/src/entrypoints/api/` for endpoint details.

The MCP endpoint at `/mcp/` follows the [Model Context Protocol specification](https://modelcontextprotocol.io).

### Development Setup

See the [Contributing Guide](https://github.com/johnkozaris/mcpHomeManager/blob/main/CONTRIBUTING.md) for full instructions on setting up a local development environment.
