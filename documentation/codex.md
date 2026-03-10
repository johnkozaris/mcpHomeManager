## Codex (OpenAI)

Add MCP Home Manager to Codex using the CLI or by editing the config file. The same configuration works for both the Codex CLI and the Codex desktop app.

### Option 1: CLI

```bash
codex mcp add homelab \
  --env MCP_HOME_KEY=YOUR_API_KEY \
  --url http://your-server:8000/mcp/ \
  --bearer-token-env-var MCP_HOME_KEY
```

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

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the key from [First Setup](first-setup).

### Verify

Run `codex mcp` to see configured servers and their status. Your homelab tools should appear in the list.

### MCP Apps

Codex supports MCP Apps (interactive HTML content). Services like Home Assistant's entity dashboard and Paperless document search render as interactive panels in your conversation.

### When Services Change

Codex caches the tool list at startup. When you connect or remove services in MCP Home Manager, restart Codex to pick up the new tools.
