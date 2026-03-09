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
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation("agents", { keyPrefix: "page" });
  const mcpEndpoint = getMcpEndpoint();
  const { data: currentUser } = useCurrentUser();
  const [apiKey, setApiKey] = useState<string | null>(null);

  useEffect(() => {
    if (currentUser?.has_api_key) {
      api.auth.getApiKey().then((d) => setApiKey(d.api_key)).catch(() => {});
    }
  }, [currentUser?.has_api_key]);

  const keyPlaceholder = apiKey ?? t("placeholders.apiKey");
  const jsonConfig = buildMcpJsonConfig(mcpEndpoint, apiKey);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-header">{t("title")}</h1>
        <p className="page-description max-w-xl">
          {t("description")}
        </p>
        <p className="text-2xs text-ink-faint mt-1.5 max-w-xl leading-relaxed">
          {t("restartNote")}
        </p>
      </div>

      <McpEndpointBar apiKey={apiKey} />

      <div className="space-y-3">
        <AgentCard
          name={t("cards.claudeDesktop.name")}
          icon={Sparkles}
          color="var(--terra)"
          bg="var(--terra-bg)"
          badge={t("cards.claudeDesktop.badge")}
        >
          <Guide color="var(--terra)">
            <Step>
              {t("cards.claudeDesktop.steps.step1.before")}{" "}
              <strong>{t("cards.claudeDesktop.steps.step1.settings")}</strong>{" "}
              {t("cards.claudeDesktop.steps.step1.middle")}{" "}
              <strong>{t("cards.claudeDesktop.steps.step1.developer")}</strong>{" "}
              {t("cards.claudeDesktop.steps.step1.and")}{" "}
              <strong>{t("cards.claudeDesktop.steps.step1.editConfig")}</strong>
            </Step>
            <Step>
              {t("cards.claudeDesktop.steps.step2.beforeFile")}{" "}
              <code className="text-xs font-mono text-terra">
                claude_desktop_config.json
              </code>
              {t("cards.claudeDesktop.steps.step2.afterFile")}{" "}
              <code className="font-mono text-terra">"homelab"</code>
              {t("cards.claudeDesktop.steps.step2.afterHomelab")}{" "}
              <code className="font-mono text-terra">"mcpServers"</code>
              {t("cards.claudeDesktop.steps.step2.afterMcpServers")}
            </Step>
          </Guide>
          <TerminalBlock code={jsonConfig} label="claude_desktop_config.json" />
          <Guide color="var(--terra)">
            <Step>
              {t("cards.claudeDesktop.steps.step3.before")}{" "}
              <strong>{t("cards.claudeDesktop.steps.step3.emphasis")}</strong>{" "}
              {t("cards.claudeDesktop.steps.step3.after")}
            </Step>
            <Step>
              {t("cards.claudeDesktop.steps.step4")}
            </Step>
            <Step>
              {t("cards.claudeDesktop.steps.step5.prefix")}{" "}
              <em className="text-ink-secondary">
                {t("cards.claudeDesktop.steps.step5.exampleRepos")}
              </em>{" "}
              {t("cards.claudeDesktop.steps.step5.or")}{" "}
              <em className="text-ink-secondary">
                {t("cards.claudeDesktop.steps.step5.examplePaperless")}
              </em>
            </Step>
          </Guide>
          <p className="text-xs text-ink-tertiary">
            {t("cards.claudeDesktop.configPath")}
          </p>
        </AgentCard>

        <AgentCard
          name={t("cards.claudeCode.name")}
          icon={Terminal}
          color="var(--terra)"
          bg="var(--terra-bg)"
        >
          <Guide color="var(--terra)">
            <Step>
              {t("cards.claudeCode.steps.step1")}
            </Step>
          </Guide>
          <TerminalBlock
            code={`claude mcp add homelab --transport http --header "Authorization: Bearer ${keyPlaceholder}" ${mcpEndpoint}`}
            label={t("cards.claudeCode.terminalLabel")}
          />
          <Guide color="var(--terra)">
            <Step>
              {t("cards.claudeCode.steps.step2.before")}{" "}
              <code className="text-xs font-mono text-terra">
                claude mcp list
              </code>{" "}
              {t("cards.claudeCode.steps.step2.after")}
            </Step>
            <Step>
              {t("cards.claudeCode.steps.step3")}
            </Step>
          </Guide>
          <p className="text-xs text-ink-tertiary">
            {t("cards.claudeCode.removePrefix")}{" "}
            <code className="font-mono text-terra">
              claude mcp remove homelab
            </code>
          </p>
        </AgentCard>

        <AgentCard
          name={t("cards.cursor.name")}
          icon={Code2}
          color="var(--info)"
          bg="var(--info-bg)"
        >
          <Guide color="var(--info)">
            <Step>
              {t("cards.cursor.steps.step1.before")}{" "}
              <code className="text-xs font-mono text-terra">
                .cursor/mcp.json
              </code>{" "}
              {t("cards.cursor.steps.step1.after")}
            </Step>
          </Guide>
          <TerminalBlock code={jsonConfig} label=".cursor/mcp.json" />
          <Guide color="var(--info)">
            <Step>
              {t("cards.cursor.steps.step2")}
            </Step>
            <Step>
              {t("cards.cursor.steps.step3")}
            </Step>
          </Guide>
        </AgentCard>

        <AgentCard
          name={t("cards.chatgpt.name")}
          icon={MonitorSmartphone}
          color="var(--sage)"
          bg="var(--sage-bg)"
        >
          <Guide color="var(--sage)">
            <Step>
              {t("cards.chatgpt.steps.step1.before")}{" "}
              <strong>{t("cards.chatgpt.steps.step1.settings")}</strong>{" "}
              {t("cards.chatgpt.steps.step1.middle")}{" "}
              <strong>{t("cards.chatgpt.steps.step1.appsAndConnectors")}</strong>{" "}
              {t("cards.chatgpt.steps.step1.after")}{" "}
              <strong>{t("cards.chatgpt.steps.step1.developerMode")}</strong>{" "}
              {t("cards.chatgpt.steps.step1.suffix")}
            </Step>
            <Step>
              {t("cards.chatgpt.steps.step2.before")}{" "}
              <strong>{t("cards.chatgpt.steps.step2.create")}</strong>{" "}
              {t("cards.chatgpt.steps.step2.and")}{" "}
              <strong>{t("cards.chatgpt.steps.step2.mcpServer")}</strong>
            </Step>
            <Step>
              {t("cards.chatgpt.steps.step3.before")}{" "}
              <code className="text-xs font-mono text-terra">
                {mcpEndpoint}
              </code>
            </Step>
            <Step>
              {t("cards.chatgpt.steps.step4.before")}{" "}
              <strong>{t("cards.chatgpt.steps.step4.create")}</strong>
              {t("cards.chatgpt.steps.step4.after")}
            </Step>
          </Guide>
          <div className="p-3 rounded-lg bg-clay-bg border border-clay text-sm text-clay">
            <strong>{t("cards.chatgpt.note.label")}</strong>{" "}
            {t("cards.chatgpt.note.body")}
          </div>
        </AgentCard>

        <AgentCard
          name={t("cards.openWebui.name")}
          icon={Globe}
          color="var(--clay)"
          bg="var(--clay-bg)"
        >
          <Guide color="var(--clay)">
            <Step>
              {t("cards.openWebui.steps.step1.before")}{" "}
              <strong>{t("cards.openWebui.steps.step1.adminPanel")}</strong>{" "}
              {t("cards.openWebui.steps.step1.and")}{" "}
              <strong>{t("cards.openWebui.steps.step1.settings")}</strong>{" "}
              {t("cards.openWebui.steps.step1.then")}{" "}
              <strong>{t("cards.openWebui.steps.step1.tools")}</strong>
            </Step>
            <Step>
              {t("cards.openWebui.steps.step2.before")}{" "}
              <strong>{t("cards.openWebui.steps.step2.addMcpConnection")}</strong>
              {t("cards.openWebui.steps.step2.after")}{" "}
              <code className="text-xs font-mono text-terra">
                {mcpEndpoint}
              </code>
            </Step>
            <Step>
              {t("cards.openWebui.steps.step3")}
            </Step>
            <Step>
              {t("cards.openWebui.steps.step4.before")}{" "}
              <strong>{t("cards.openWebui.steps.step4.save")}</strong>
              {t("cards.openWebui.steps.step4.after")}
            </Step>
          </Guide>
        </AgentCard>

        <AgentCard
          name={t("cards.otherClients.name")}
          icon={Puzzle}
          color="var(--stone)"
          bg="var(--stone-bg)"
        >
          <p className="text-sm text-ink-secondary">
            {t("cards.otherClients.description")}
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              {
                id: "transport",
                label: t("cards.otherClients.details.transport.label"),
                value: t("cards.otherClients.details.transport.value"),
              },
              {
                id: "auth",
                label: t("cards.otherClients.details.auth.label"),
                value: t("cards.otherClients.details.auth.value"),
              },
              {
                id: "discovery",
                label: t("cards.otherClients.details.discovery.label"),
                value: t("cards.otherClients.details.discovery.value"),
              },
            ].map((item) => (
              <div
                key={item.id}
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
              {t("cards.otherClients.sse.before")}{" "}
              <code className="font-mono text-terra">/sse</code>
              {t("cards.otherClients.sse.after")}
            </p>
          </div>
        </AgentCard>
      </div>
    </div>
  );
}
