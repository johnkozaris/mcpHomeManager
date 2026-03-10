## Generic REST

The Generic REST adapter lets you connect any REST API to MCP Home Manager — even services without a built-in adapter. Define custom tools that map to API endpoints, and your AI agent can call them like any other MCP tool.

### When to Use Generic REST

- Your service is not one of the 17 built-in types
- You want to access additional API endpoints on a service that already has a built-in adapter
- You want to integrate an internal or custom API

### Setting Up a Generic REST Service

:::steps
1. **Go to Services → Connect Service**
2. **Select "Generic REST"** as the service type
3. **Enter the base URL** — The root URL of the API (e.g., `http://192.168.1.100:5000/api`)
4. **Enter credentials** — Choose the appropriate auth method (see below)
5. **Save** — The connection is tested against the base URL
:::

### Authentication Methods

| Method | Credential Format | How It's Sent |
|--------|-------------------|---------------|
| Bearer token | `your-token` | `Authorization: Bearer your-token` |
| API key | `your-key` (configure header name in service settings) | Custom header (e.g., `X-API-Key: your-key`) |
| Basic auth | `username:password` | `Authorization: Basic base64(user:pass)` |
| None | Leave empty | No auth header |

### Adding Tools Manually

After creating the service, add custom tools that map to API endpoints:

:::steps
1. **Open the service** — Click on your Generic REST service
2. **Click "Add Custom Tool"**
3. **Fill in the tool definition:**
   - **Name** — A unique identifier (e.g., `get_users`). This is what your AI agent sees.
   - **Description** — What the tool does. Be descriptive — your AI agent uses this to decide when to call it.
   - **HTTP Method** — GET, POST, PUT, PATCH, or DELETE
   - **Path Template** — The endpoint path relative to the base URL. Use `{param}` for path parameters (e.g., `/users/{user_id}`)
   - **Parameter Schema** — JSON Schema defining the tool's parameters
4. **Save** — The tool is immediately available via MCP
:::

### Path Parameter Interpolation

Use `{param_name}` placeholders in path templates. MCP Home Manager replaces them with values from the tool's parameters at call time.

Example path template: `/repos/{owner}/{repo}/issues`

When your AI agent calls this tool with `owner: "my-org"` and `repo: "my-project"`, the request goes to `/repos/my-org/my-project/issues`.

### Importing from OpenAPI

If your API has an OpenAPI (Swagger) specification, you can auto-generate tools:

:::steps
1. **Open the service** — Click on your Generic REST service
2. **Click "Import OpenAPI"**
3. **Provide the spec** — Paste a URL to the OpenAPI JSON/YAML, or upload a file
4. **Review generated tools** — Each API endpoint becomes a tool
5. **Enable the ones you want** — Toggle tools on or off
:::

See the [OpenAPI Import](openapi-import) guide for more details.

### Example: Adding a Custom API

Suppose you have a home automation API at `http://192.168.1.50:5000` that controls your sprinkler system.

**Step 1:** Add a Generic REST service with:
- URL: `http://192.168.1.50:5000`
- Auth: Bearer token

**Step 2:** Add a tool:
- Name: `get_sprinkler_status`
- Description: "Get the current status of all sprinkler zones"
- Method: GET
- Path: `/api/zones`

**Step 3:** Add another tool:
- Name: `toggle_sprinkler_zone`
- Description: "Turn a sprinkler zone on or off"
- Method: POST
- Path: `/api/zones/{zone_id}/toggle`
- Parameters: `zone_id` (string, required)

Now your AI agent can check sprinkler status and control zones.

### Security

MCP Home Manager applies several security measures to Generic REST requests:

- **Cloud metadata blocked** — Requests to cloud metadata endpoints (169.254.169.254, metadata.google.internal, etc.) are blocked to prevent SSRF
- **DNS rebinding protection** — DNS resolution is checked to prevent rebinding attacks
- **Path traversal protection** — Path parameters are validated to prevent directory traversal
- **Dangerous headers blocked** — Headers like `Host`, `Content-Length`, and `Transfer-Encoding` cannot be set via custom headers

### Related

- [Custom Tools](custom-tools) — JSON Schema reference for tool parameter definitions
- [OpenAPI Import](openapi-import) — Detailed guide for importing from OpenAPI specs
