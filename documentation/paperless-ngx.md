## Paperless-ngx

Search and browse your document archive through your AI agent. Find documents by content, tags, correspondents, or document type.

### What You Can Do

- Full-text search across all documents
- View document metadata and content
- List and filter by tags, correspondents, and document types

### Prerequisites

- Paperless-ngx instance accessible from MCP Home Manager
- An API token

### Getting Your Token

:::steps
1. **Open Paperless-ngx** — Navigate to your Paperless-ngx instance
2. **Go to Settings** — Click the gear icon or navigate to Administration
3. **Create an API token** — Under "API" or via the Django admin at `/admin/authtoken/tokenproxy/`
4. **Copy the token** — Save it securely

Alternatively, create a token from the command line:

```bash
docker exec -it paperless python manage.py create_api_token your-username
```
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** Paperless-ngx
- **URL:** Your Paperless-ngx URL (e.g., `http://192.168.1.100:8000`)
- **Credentials:** Paste your API token

### Available Tools

:::tools
- `paperless_search_documents` — Full-text search across all documents with optional filtering
- `paperless_get_document` — Get detailed metadata and content for a specific document
- `paperless_list_tags` — List all tags in your Paperless-ngx instance
- `paperless_list_correspondents` — List all correspondents
- `paperless_list_document_types` — List all document types
:::

### MCP App

- `paperless_document_search` — Interactive HTML search interface for browsing documents. Available in MCP clients that support apps (e.g., Claude Desktop).

### Limitations

- **Read-only** — Cannot upload, edit, or delete documents through MCP
- **Metadata only** — Cannot download the actual file content (PDF, image, etc.). Returns document metadata, text content, and tags.

### Example Prompts

- "Search my documents for electricity bills from 2025"
- "What tags do I have in Paperless?"
- "Show me the details of document #42"
- "Find all documents from the tax office"
- "List my document types"
