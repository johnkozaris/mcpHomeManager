## Forgejo

Manage your Forgejo repositories, issues, and pull requests through your AI agent.

### What You Can Do

- List and search repositories
- View repository details
- Create and list issues
- Create and list pull requests

### Prerequisites

- Forgejo instance accessible from MCP Home Manager
- A personal access token with appropriate scopes

### Getting Your Token

:::steps
1. **Open Forgejo** — Navigate to your Forgejo instance
2. **Go to Settings** — Click your avatar → Settings → Applications
3. **Generate a new token** — Under "Manage Access Tokens" → enter a name, select scopes
4. **Select scopes** — For read-only access: `read:repository`, `read:issue`. For write access (create issues/PRs): also add `write:repository`, `write:issue`
5. **Generate and copy the token** — Save it securely
:::

### Connecting

In MCP Home Manager, go to **Services → Connect Service**:
- **Type:** Forgejo
- **URL:** Your Forgejo URL (e.g., `http://192.168.1.100:3000`)
- **Credentials:** Paste your personal access token

### Available Tools

:::tools
- `forgejo_list_repos` — List repositories accessible with your token
- `forgejo_get_repo` — Get detailed information about a specific repository
- `forgejo_list_issues` — List issues for a repository
- `forgejo_create_issue` — Create a new issue in a repository
- `forgejo_list_pull_requests` — List pull requests for a repository
- `forgejo_create_pull_request` — Create a new pull request
- `forgejo_search_repos` — Search repositories by keyword
:::

### MCP App

- `forgejo_repo_browser` — Interactive HTML repository browser. Available in MCP clients that support apps (e.g., Claude Desktop).

### Limitations

- **No file content access** — Cannot read file contents from repositories
- **No PR merging** — Cannot merge pull requests through MCP
- **Write scopes required** — `forgejo_create_issue` and `forgejo_create_pull_request` require a token with write scopes

### Example Prompts

- "List all my Forgejo repositories"
- "Show me the open issues on the my-project repo"
- "Create an issue titled 'Fix login bug' on my-project"
- "Search for repos related to automation"
- "What pull requests are open on my-project?"
