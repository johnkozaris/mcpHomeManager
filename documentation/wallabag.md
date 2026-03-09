## Wallabag

Manage your read-it-later articles through your AI agent. Save URLs, search entries, manage tags, and browse your reading list.

### What You Can Do

- List and search saved articles
- Save new URLs for later reading
- Delete entries
- Manage tags on entries

### Prerequisites

- Wallabag instance accessible from MCP Home Manager
- OAuth2 API client credentials and your user account

### Getting Your Credentials

:::steps
1. **Open Wallabag** — Navigate to your Wallabag instance
2. **Go to API clients** — Settings → API clients management → Create a new client
3. **Create a client** — Give it a name (e.g., `mcp-home-manager`). Note the generated **Client ID** and **Client Secret**.
4. **Format your credentials** — Combine into the format: `client_id:client_secret:username:password`
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** Wallabag
- **URL:** Your Wallabag URL (e.g., `http://192.168.1.100:8080`)
- **Credentials:** `client_id:client_secret:username:password` format (e.g., `1_abc123:xyz789:user:your-password`)

### Available Tools

:::tools
- `wallabag_list_entries` — List saved entries with optional filtering
- `wallabag_get_entry` — Get the full content of a specific entry
- `wallabag_save_url` — Save a new URL to Wallabag
- `wallabag_delete_entry` — Delete a saved entry
- `wallabag_list_tags` — List all tags
- `wallabag_tag_entry` — Add tags to an entry
- `wallabag_search` — Search entries by keyword
:::

### Limitations

- **OAuth2 flow** — Uses a full OAuth2 password grant flow. Tokens auto-refresh, but the first connection may be slower while tokens are exchanged.
- **Four-part credentials** — The credential format requires all four components (`client_id:client_secret:username:password`). Missing any part will cause authentication failure.

### Example Prompts

- "Show me my saved articles"
- "Save this URL for later: https://example.com/article"
- "Search my Wallabag for articles about Docker"
- "Tag article #42 with 'devops' and 'homelab'"
- "What tags do I have in Wallabag?"
