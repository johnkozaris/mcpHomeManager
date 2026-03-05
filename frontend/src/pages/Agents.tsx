import { TerminalBlock } from "@/components/ui/TerminalBlock";
import { Badge } from "@/components/ui/Badge";
import { McpEndpointBar } from "@/components/ui/McpEndpointBar";
import { buildMcpJsonConfig, getMcpEndpoint } from "@/lib/utils";
import { useCurrentUser } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import {
  Terminal,
  Globe,
  Sparkles,
  MonitorSmartphone,
  Code2,
  Puzzle,
  ChevronDown,
} from "lucide-react";
import { useState, useEffect } from "react";

function AgentCard({
  name,
  icon: Icon,
  color,
  bg,
  badge,
  children,
}: {
  name: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
  bg: string;
  badge?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-4 p-5 text-left hover:bg-surface-hover transition-colors cursor-pointer group"
      >
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: bg, color }}
        >
          <Icon size={18} />
        </div>
        <div className="flex items-center gap-2 flex-1">
          <span className="text-base font-bold text-ink group-hover:text-terra transition-colors">
            {name}
          </span>
          {badge && <Badge variant="brand">{badge}</Badge>}
        </div>
        <div
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all shrink-0 ${open ? "bg-terra text-white rotate-180" : "bg-canvas-tertiary text-ink-tertiary group-hover:bg-canvas-hover"}`}
        >
          <ChevronDown size={16} />
        </div>
      </button>
      <div
        className={`grid transition-[grid-template-rows] duration-200 ease-out ${open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
      >
        <div className="overflow-hidden">
          <div className="px-6 pb-6 pt-4 space-y-4">{children}</div>
        </div>
      </div>
    </div>
  );
}

function Guide({
  color,
  children,
}: {
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-l-2 pl-4 space-y-2" style={{ borderColor: color }}>
      {children}
    </div>
  );
}

function Step({ children }: { children: React.ReactNode }) {
  return <p className="text-base text-ink leading-relaxed">{children}</p>;
}

export function Agents() {
  const mcpEndpoint = getMcpEndpoint();
  const { data: currentUser } = useCurrentUser();
  const [apiKey, setApiKey] = useState<string | null>(null);

  useEffect(() => {
    if (currentUser?.has_api_key) {
      api.auth.getApiKey().then((d) => setApiKey(d.api_key)).catch(() => {});
    }
  }, [currentUser?.has_api_key]);

  const keyPlaceholder = apiKey ?? "YOUR_API_KEY";
  const jsonConfig = buildMcpJsonConfig(mcpEndpoint, apiKey);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-header">Connect AI Agents</h1>
        <p className="page-description max-w-xl">
          Add your MCP endpoint to any AI client below. Once connected, your
          homelab tools will be discovered automatically.
        </p>
      </div>

      <McpEndpointBar apiKey={apiKey} />

      <div className="space-y-3">
        <AgentCard
          name="Claude Desktop"
          icon={Sparkles}
          color="var(--terra)"
          bg="var(--terra-bg)"
          badge="Recommended"
        >
          <Guide color="var(--terra)">
            <Step>
              Go to <strong>Settings</strong> (gear icon) →{" "}
              <strong>Developer</strong> → <strong>Edit Config</strong>
            </Step>
            <Step>
              This opens{" "}
              <code className="text-xs font-mono text-terra">
                claude_desktop_config.json
              </code>
              . If the file already has other MCP servers, add the{" "}
              <code className="font-mono text-terra">"homelab"</code> entry
              inside the existing{" "}
              <code className="font-mono text-terra">"mcpServers"</code> object.
              Otherwise, replace the file contents with:
            </Step>
          </Guide>
          <TerminalBlock code={jsonConfig} label="claude_desktop_config.json" />
          <Guide color="var(--terra)">
            <Step>
              Save the file and <strong>completely quit</strong> Claude Desktop
              (not just close the window — quit from the menu bar/system tray),
              then reopen it
            </Step>
            <Step>
              You should see a hammer icon in the chat input — click it to
              verify your homelab tools are loaded
            </Step>
            <Step>
              Try:{" "}
              <em className="text-ink-secondary">
                "What repos do I have on Forgejo?"
              </em>{" "}
              or{" "}
              <em className="text-ink-secondary">
                "Search my Paperless documents for invoices"
              </em>
            </Step>
          </Guide>
          <p className="text-xs text-ink-tertiary">
            Config path — macOS: ~/Library/Application Support/Claude/ ·
            Windows: %APPDATA%\Claude\
          </p>
        </AgentCard>

        <AgentCard
          name="Claude Code"
          icon={Terminal}
          color="var(--terra)"
          bg="var(--terra-bg)"
        >
          <Guide color="var(--terra)">
            <Step>
              Register your homelab MCP server globally with the command below
              (available in all projects):
            </Step>
          </Guide>
          <TerminalBlock
            code={`claude mcp add homelab --transport http --header "Authorization: Bearer ${keyPlaceholder}" ${mcpEndpoint}`}
            label="Terminal"
          />
          <Guide color="var(--terra)">
            <Step>
              Verify with{" "}
              <code className="text-xs font-mono text-terra">
                claude mcp list
              </code>{" "}
              — you should see "homelab" in the output
            </Step>
            <Step>
              Your homelab tools are now available in every session
              automatically
            </Step>
          </Guide>
          <p className="text-xs text-ink-tertiary">
            To remove later:{" "}
            <code className="font-mono text-terra">
              claude mcp remove homelab
            </code>
          </p>
        </AgentCard>

        <AgentCard
          name="Cursor"
          icon={Code2}
          color="var(--info)"
          bg="var(--info-bg)"
        >
          <Guide color="var(--info)">
            <Step>
              Create{" "}
              <code className="text-xs font-mono text-terra">
                .cursor/mcp.json
              </code>{" "}
              in your project root with the following content:
            </Step>
          </Guide>
          <TerminalBlock code={jsonConfig} label=".cursor/mcp.json" />
          <Guide color="var(--info)">
            <Step>
              Restart Cursor (Cmd+Q / close and reopen). Your tools should
              appear in the AI panel (Cmd+L / Ctrl+L) under "Available Tools"
            </Step>
            <Step>
              If tools don't appear, check the MCP status indicator in the
              bottom status bar
            </Step>
          </Guide>
        </AgentCard>

        <AgentCard
          name="ChatGPT"
          icon={MonitorSmartphone}
          color="var(--sage)"
          bg="var(--sage-bg)"
        >
          <Guide color="var(--sage)">
            <Step>
              Go to <strong>Settings</strong> →{" "}
              <strong>Apps & Connectors</strong> → enable{" "}
              <strong>Developer mode</strong> under "Advanced settings"
            </Step>
            <Step>
              Back in "Apps & Connectors", click <strong>Create</strong> →
              select <strong>MCP Server</strong>
            </Step>
            <Step>
              Enter a name like "My Homelab" and paste your endpoint:{" "}
              <code className="text-xs font-mono text-terra">
                {mcpEndpoint}
              </code>
            </Step>
            <Step>
              Click <strong>Create</strong>. New conversations will
              automatically discover your homelab tools
            </Step>
          </Guide>
          <div className="p-3 rounded-lg bg-clay-bg border border-clay text-sm text-clay">
            <strong>Note:</strong> ChatGPT requires a publicly accessible
            endpoint. Use the included Caddy config or a tunnel service like
            Cloudflare Tunnel if your server is local-only.
          </div>
        </AgentCard>

        <AgentCard
          name="Open WebUI"
          icon={Globe}
          color="var(--clay)"
          bg="var(--clay-bg)"
        >
          <Guide color="var(--clay)">
            <Step>
              Go to <strong>Admin Panel</strong> → <strong>Settings</strong> →{" "}
              <strong>Tools</strong>
            </Step>
            <Step>
              Click <strong>Add MCP Connection</strong>, enter a name and paste
              your endpoint:{" "}
              <code className="text-xs font-mono text-terra">
                {mcpEndpoint}
              </code>
            </Step>
            <Step>
              If using API key auth, enter your key in the authentication field
            </Step>
            <Step>
              Click <strong>Save</strong> — Open WebUI will test the connection
              and discover your tools. They're now available to all users with
              any LLM
            </Step>
          </Guide>
        </AgentCard>

        <AgentCard
          name="Other MCP Clients"
          icon={Puzzle}
          color="var(--stone)"
          bg="var(--stone-bg)"
        >
          <p className="text-sm text-ink-secondary">
            If your MCP client asks for specific connection details:
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Transport", value: "Streamable HTTP" },
              { label: "Auth", value: "Authorization: Bearer" },
              { label: "Discovery", value: "Automatic" },
            ].map((item) => (
              <div
                key={item.label}
                className="p-3 rounded-xl bg-canvas text-center"
              >
                <p className="text-2xs font-bold uppercase tracking-wider text-ink-tertiary mb-1">
                  {item.label}
                </p>
                <p className="text-sm font-semibold text-ink">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="space-y-1.5 text-sm text-ink-secondary">
            <p>
              For SSE-only clients, append{" "}
              <code className="font-mono text-terra">/sse</code> to the endpoint
              URL. The base URL must be reachable from wherever your AI client
              runs.
            </p>
          </div>
        </AgentCard>
      </div>
    </div>
  );
}
