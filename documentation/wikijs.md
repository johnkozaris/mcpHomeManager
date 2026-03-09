## Wiki.js

Manage your wiki pages through your AI agent. Search, read, create, and update wiki content.

### What You Can Do

- List and search wiki pages
- Read full page content
- Create new pages
- Update existing pages
- List wiki users (admin only)

### Prerequisites

- Wiki.js instance accessible from MCP Home Manager
- An API key with appropriate permissions

### Getting Your API Key

:::steps
1. **Open Wiki.js** — Navigate to your Wiki.js instance
2. **Go to Administration** — Click the admin menu
3. **Navigate to API Access** — Under "System" → API Access
4. **Create a new API key** — Click "Create API Key", set an expiration if desired
5. **Copy the key** — Save it securely
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** Wiki.js
- **URL:** Your Wiki.js URL (e.g., `http://192.168.1.100:3000`)
- **Credentials:** Paste your API key

### Available Tools

:::tools
- `wikijs_list_pages` — List all wiki pages
- `wikijs_get_page` — Get the full content of a specific page
- `wikijs_search` — Search pages by keyword
- `wikijs_create_page` — Create a new wiki page
- `wikijs_update_page` — Update an existing wiki page
- `wikijs_list_users` — List wiki users (requires admin API key)
:::

### Limitations

- **Admin-only tools** — `wikijs_list_users` requires an admin-level API key
- **Write permissions** — `wikijs_create_page` and `wikijs_update_page` require an API key with write permissions
- **GraphQL backend** — Wiki.js uses GraphQL internally. The adapter translates MCP tool calls to GraphQL queries.

### Example Prompts

- "List all pages in my wiki"
- "Show me the content of the 'Getting Started' page"
- "Search for pages about networking"
- "Create a new wiki page titled 'Server Setup Guide'"
- "Update the 'Docker' page with the new configuration"
