## FreshRSS

Read and manage your RSS feeds through your AI agent. Browse articles, manage read status, and add new feeds.

### What You Can Do

- List feeds and get unread counts
- Read articles (all, unread, or starred)
- Mark articles as read
- Star and unstar articles
- Add new RSS feeds

### Prerequisites

- FreshRSS instance accessible from MCP Home Manager
- Your FreshRSS username and password
- The Google Reader compatible API enabled in FreshRSS

### Enabling the API

:::steps
1. **Open FreshRSS** — Navigate to your FreshRSS instance
2. **Go to Settings** — Configuration → Authentication
3. **Enable API access** — Check "Allow API access" and set an API password
4. **Verify** — The API endpoint is available at `your-freshrss-url/api/greader.php`
:::

### Connecting

In MCP Home Manager, go to **Services → Add Service**:
- **Type:** FreshRSS
- **URL:** Your FreshRSS URL (e.g., `http://192.168.1.100:8080`). Can point to the root or directly to `/api/greader.php`.
- **Credentials:** `username:password` format (e.g., `admin:your-api-password`)

### Available Tools

:::tools
- `freshrss_list_feeds` — List all subscribed RSS feeds
- `freshrss_get_unread_count` — Get unread article counts per feed
- `freshrss_get_articles` — Get articles with optional filtering
- `freshrss_get_unread` — Get unread articles
- `freshrss_mark_read` — Mark articles as read
- `freshrss_star_article` — Star or unstar an article
- `freshrss_add_feed` — Subscribe to a new RSS feed
:::

### Limitations

- **Google Reader API** — Uses the Google Reader-compatible API, not a native FreshRSS API. Some advanced FreshRSS features may not be accessible.
- **No feed removal** — Cannot unsubscribe from feeds or edit feed settings through MCP
- **API password** — The API password may be different from your login password, depending on your FreshRSS configuration

### Example Prompts

- "What are my unread article counts?"
- "Show me unread articles from the tech feeds"
- "Mark all articles from today as read"
- "Star this article about Docker"
- "Subscribe to this RSS feed: https://example.com/feed.xml"
