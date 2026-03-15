## Codex (OpenAI)

Add MCP Home Manager to Codex using the CLI or by editing the config file. The same configuration works for both the Codex CLI and the Codex desktop app.

:::info Config Precedence
Global config (`~/.codex/config.toml`) applies everywhere. Project config (`.codex/config.toml`) overrides it for that project.
:::

### Option 1: CLI

```bash
codex mcp add homelab \
  --env MCP_HOME_KEY=YOUR_API_KEY \
  --url http://your-server:8000/mcp/ \
  --bearer-token-env-var MCP_HOME_KEY
```

The `--bearer-token-env-var` flag tells Codex which environment variable holds the API key. Codex reads it at runtime and sends it as a `Bearer` token in the `Authorization` header.

### Option 2: Config File

Add the following to `~/.codex/config.toml` (global) or `.codex/config.toml` (project-scoped):

```toml
[mcp_servers.homelab]
url = "http://your-server:8000/mcp/"
bearer_token_env_var = "MCP_HOME_KEY"
```

Then set the environment variable with your API key:

```bash
export MCP_HOME_KEY="YOUR_API_KEY"
```

Use the URL from your [installation](installation) (e.g., `http://192.168.1.100:8000/mcp/`) and the API key from [First Setup](first-setup).

### Verify

Run `codex mcp` to see configured servers and their status. Your homelab tools should appear in the list.

### MCP Apps

Codex supports MCP Apps (interactive HTML content). Services like Home Assistant's entity dashboard and Paperless document search render as interactive panels in your conversation.

### When Services Change

MCP Home Manager registers new tools immediately. Codex caches tools at startup — restart it to see changes.
