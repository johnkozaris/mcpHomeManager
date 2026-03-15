## Immich

Search and browse your photo library through your AI agent. Find photos using natural language, browse albums, and view asset metadata.

### What You Can Do

- Search photos using natural language (powered by CLIP/ML — CLIP is the image recognition AI that powers Immich's search)
- Browse albums and their contents
- View detailed asset metadata
- Check server storage statistics

### Prerequisites

- Immich instance accessible from MCP Home Manager
- An API key

### Getting Your API Key

:::steps
1. **Open Immich** — Navigate to your Immich instance
2. **Go to Account Settings** — Click your avatar → Account Settings
3. **Create an API key** — Under "API Keys" → New API Key
4. **Name it** — Give it a descriptive name (e.g., `mcp-home-manager`)
5. **Copy the key** — Save it securely
:::

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Immich
- **URL:** Your Immich URL (e.g., `http://192.168.1.100:2283`)
- **Credentials:** Paste your API key

### Available Tools

:::tools
- `immich_search_photos` — Search photos using natural language queries (uses CLIP, Immich's image recognition AI model)
- `immich_get_asset` — Get detailed metadata for a specific asset (photo or video)
- `immich_list_albums` — List all albums
- `immich_get_album` — Get album details and its assets
- `immich_server_stats` — Get server storage statistics (requires admin API key)
:::

### Limitations

- **ML-based search** — `immich_search_photos` uses Immich's CLIP model (the image recognition AI that powers visual search) for natural language search. Results depend on how well the model understands your query, not keyword matching.
- **Admin stats** — `immich_server_stats` requires an admin-level API key. Regular user keys will get a permission error.
- **Read-only** — Cannot upload, delete, or modify photos through MCP
- **Metadata only** — Returns asset metadata and URLs, not actual image content

### Example Prompts

- "Find photos of sunsets from last summer"
- "List all my photo albums"
- "Show me the details of this photo" (provide asset ID)
- "How much storage is Immich using?"
- "Find pictures with dogs in the park"
