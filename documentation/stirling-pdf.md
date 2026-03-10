## Stirling PDF

Check the status and available operations of your Stirling PDF instance through your AI agent.

### What You Can Do

- Check Stirling PDF health status
- List available PDF operations

### Prerequisites

- Stirling PDF instance accessible from MCP Home Manager
- An API key (if authentication is enabled)

### Getting Your API Key

:::steps
1. **Open Stirling PDF** — Navigate to your Stirling PDF instance
2. **Go to Settings** — Access the admin settings
3. **Find your API key** — Under security or API settings
4. **Copy the key** — Save it securely
:::

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Stirling PDF
- **URL:** Your Stirling PDF URL (e.g., `http://192.168.1.100:8080`)
- **Credentials:** Your API key

### Available Tools

:::tools
- `stirling_health` — Check the health status of the Stirling PDF instance
- `stirling_get_operations` — List all available PDF operations (merge, split, OCR, etc.)
:::

### Limitations

- **Very limited MCP integration** — Stirling PDF operations (merge, split, rotate, OCR, compress, etc.) require file uploads via multipart/form-data, which is not supported through MCP. This adapter provides status and operation listing only.
- **Use the native web UI** — For actual PDF processing, use the Stirling PDF web UI directly. The MCP adapter is useful for checking service availability and listing what operations are supported.

### Example Prompts

- "Is Stirling PDF running?"
- "What PDF operations are available?"
