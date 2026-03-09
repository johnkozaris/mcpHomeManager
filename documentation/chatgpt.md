## ChatGPT

ChatGPT's MCP support is still evolving. As of early 2026, MCP integration in ChatGPT is limited compared to Claude Desktop or Claude Code.

### Current Status

ChatGPT has begun rolling out MCP support, but availability and configuration may vary depending on your ChatGPT plan and region. Check [OpenAI's documentation](https://platform.openai.com/docs) for the latest on MCP support.

### Configuration

If MCP support is available in your ChatGPT setup, the configuration follows the standard pattern:

- **Endpoint URL:** `http://your-server:8000/mcp/`
- **Authentication:** `Authorization: Bearer YOUR_API_KEY`

Replace `your-server` with the hostname or IP of your MCP Home Manager instance, and `YOUR_API_KEY` with the API key from [First Setup](first-setup).

### Recommended Alternatives

For the most complete MCP experience, consider:

- [Claude Desktop](claude-desktop) — Full MCP support including interactive apps
- [Claude Code](claude-code) — CLI-based MCP integration
- [Cursor](cursor) — IDE with MCP support
