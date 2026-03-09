## Nextcloud

Browse files and notes on your Nextcloud instance through your AI agent.

### What You Can Do

- List and search files in your Nextcloud storage
- Read and list notes (requires the Nextcloud Notes app)
- Check user status

### Prerequisites

- Nextcloud instance accessible from MCP Home Manager
- An app password (not your regular login password)

### Getting Your App Password

:::steps
1. **Open Nextcloud** — Navigate to your Nextcloud instance
2. **Go to Settings** — Click your avatar → Settings → Security
3. **Create an app password** — Under "Devices & sessions", enter a name (e.g., `mcp-home-manager`) and click "Create new app password"
4. **Copy the credentials** — You need both your username and the generated app password
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** Nextcloud
- **URL:** Your Nextcloud URL (e.g., `http://192.168.1.100:8080`)
- **Credentials:** `username:app-password` format (e.g., `user:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`)

### Available Tools

:::tools
- `nextcloud_list_files` — List files in a directory (WebDAV path listing)
- `nextcloud_search_files` — Search for files by name
- `nextcloud_list_notes` — List all notes (requires Nextcloud Notes app)
- `nextcloud_get_note` — Get the content of a specific note
- `nextcloud_user_status` — Get current user status information
:::

### Limitations

- **Notes app required** — The `nextcloud_list_notes` and `nextcloud_get_note` tools require the [Nextcloud Notes](https://apps.nextcloud.com/apps/notes) app to be installed
- **No file content** — Cannot upload or download file contents. File listing provides metadata (name, size, modified date) via WebDAV path listing only.
- **App password required** — Regular passwords may not work due to 2FA or security policies. Always use an app password.

### Example Prompts

- "List the files in my Documents folder"
- "Search for files named 'budget'"
- "Show me my Nextcloud notes"
- "What's the content of my 'Shopping List' note?"
