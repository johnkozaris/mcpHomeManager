## Portainer

Manage your Docker containers and stacks through your AI agent. View container status, start/stop containers, and read container logs.

### What You Can Do

- List environments (endpoints) and containers
- Start, stop, and restart containers
- View container details and logs
- List Docker stacks

### Prerequisites

- Portainer instance accessible from MCP Home Manager
- An API key or admin username and password

### Getting Your Credentials

**Option 1: API Key (recommended)**

:::steps
1. **Open Portainer** — Navigate to your Portainer instance
2. **Go to your account** — Click your username → My account
3. **Create an API key** — Under "Access tokens" → Add access token
4. **Name it** — Give it a descriptive name (e.g., `mcp-home-manager`)
5. **Copy the key** — Save it securely (starts with `ptr_`)
:::

**Option 2: Username and password**

Use your Portainer admin credentials in `username:password` format.

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Portainer
- **URL:** Your Portainer URL (e.g., `http://192.168.1.100:9000`)
- **Credentials:** Your API key (e.g., `ptr_abc123...`) or `username:password`

### Available Tools

:::tools
- `portainer_list_endpoints` — List all Portainer environments (endpoints)
- `portainer_list_containers` — List containers in an environment
- `portainer_get_container` — Get detailed information about a specific container
- `portainer_start_container` — Start a stopped container
- `portainer_stop_container` — Stop a running container
- `portainer_restart_container` — Restart a container
- `portainer_list_stacks` — List Docker stacks
- `portainer_get_container_logs` — Get logs from a container
:::

### Limitations

- **Endpoint ID required** — Container operations require an `endpoint_id`. Portainer calls each Docker host an "endpoint." The endpoint ID (usually `1` for single-host setups) identifies which host to manage. List endpoints first to get the ID.
- **No create/delete** — Cannot create or delete containers or stacks through MCP
- **JWT refresh** — When using username/password auth, JWT tokens auto-refresh but may have brief authentication interruptions

### Example Prompts

- "List all my Portainer environments"
- "What containers are running on endpoint 1?"
- "Show me the logs from the nginx container"
- "Restart the home-assistant container"
- "Stop the staging-app container"
