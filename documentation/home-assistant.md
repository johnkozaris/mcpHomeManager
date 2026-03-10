## Home Assistant

Control your smart home through your AI agent. Query entity states, list devices, and call Home Assistant services.

### What You Can Do

- Check the state of any entity (lights, sensors, switches, climate, etc.)
- List all entities or filter by domain
- Call Home Assistant services (turn on/off lights, set thermostat, lock doors, etc.)
- Browse available Home Assistant service definitions

### Prerequisites

- Home Assistant instance accessible from MCP Home Manager
- A long-lived access token

### Getting Your Token

:::steps
1. **Open Home Assistant** — Navigate to your Home Assistant instance
2. **Go to your profile** — Click your username in the sidebar
3. **Create a long-lived access token** — Scroll to the bottom of the profile page → "Long-lived access tokens" → Create Token
4. **Name it** — Give it a descriptive name (e.g., `mcp-home-manager`)
5. **Copy the token** — It is shown only once. Save it securely.
:::

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Home Assistant
- **URL:** Your Home Assistant URL (e.g., `http://192.168.1.100:8123`)
- **Credentials:** Paste your long-lived access token

### Available Tools

:::tools
- `ha_get_entity_state` — Get the current state and attributes of a specific entity
- `ha_list_entities` — List all entities, optionally filtered by domain (e.g., `light`, `sensor`, `switch`)
- `ha_call_service` — Call a Home Assistant service (e.g., `light.turn_on`, `climate.set_temperature`)
- `ha_get_services` — List available Home Assistant services and their parameters
:::

### MCP App

- `ha_entity_dashboard` — Interactive HTML dashboard showing entity states. Available in MCP clients that support apps (e.g., Claude Desktop).

### Limitations

- **No history or logbook access** — Cannot retrieve historical entity states or logbook entries
- **No event firing** — Cannot fire custom Home Assistant events
- **Long-lived tokens only** — Short-lived tokens expire and will cause authentication failures. Always use a long-lived access token.

### Example Prompts

- "What's the temperature in the living room?"
- "Turn off all the lights in the bedroom"
- "Is the front door locked?"
- "Set the thermostat to 21 degrees"
- "List all my motion sensors"
