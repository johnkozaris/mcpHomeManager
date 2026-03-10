## Calibre-Web

Browse your e-book library through your AI agent. Search for books, browse by author, category, or series.

### What You Can Do

- Search for books by title or keyword
- Browse books by author, category, or series
- Mark books as read or unread

### Prerequisites

- Calibre-Web instance accessible from MCP Home Manager
- Your Calibre-Web username and password

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Calibre-Web
- **URL:** Your Calibre-Web URL (e.g., `http://192.168.1.100:8083`)
- **Credentials:** `username:password` format (e.g., `admin:your-password`)

### Available Tools

:::tools
- `calibreweb_search_books` — Search for books by title or keyword
- `calibreweb_list_authors` — List authors in your library
- `calibreweb_list_categories` — List book categories
- `calibreweb_list_series` — List book series
- `calibreweb_toggle_read` — Mark a book as read or unread
:::

### Limitations

- **Form-based auth** — Calibre-Web uses HTML form-based login (session cookies), not a REST API. This means authentication may be slower than token-based services.
- **No file downloads** — Cannot download book files (EPUB, PDF, etc.) through MCP
- **OPDS health check** — The health check uses the OPDS endpoint. If OPDS is disabled in Calibre-Web settings, health checks will fail.

### Example Prompts

- "Search my library for science fiction books"
- "List all authors in my Calibre library"
- "What book series do I have?"
- "Mark 'Dune' as read"
- "List books in the 'Programming' category"
