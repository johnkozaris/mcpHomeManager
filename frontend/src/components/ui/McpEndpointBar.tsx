import { useState, useEffect } from "react";
import { Terminal, Copy, Check, Braces } from "lucide-react";
import { buildMcpJsonConfig, getMcpEndpoint } from "@/lib/utils";
import { useTranslation } from "react-i18next";

export function McpEndpointBar({ apiKey }: { apiKey?: string | null } = {}) {
  const { t } = useTranslation("components", { keyPrefix: "ui.mcpEndpointBar" });
  const mcpEndpoint = getMcpEndpoint();
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  useEffect(() => {
    if (!copiedUrl) return;
    const id = setTimeout(() => setCopiedUrl(false), 2000);
    return () => clearTimeout(id);
  }, [copiedUrl]);

  useEffect(() => {
    if (!copiedJson) return;
    const id = setTimeout(() => setCopiedJson(false), 2000);
    return () => clearTimeout(id);
  }, [copiedJson]);

  const copyUrl = () => {
    navigator.clipboard.writeText(mcpEndpoint);
    setCopiedUrl(true);
  };

  const copyJson = () => {
    navigator.clipboard.writeText(buildMcpJsonConfig(mcpEndpoint, apiKey));
    setCopiedJson(true);
  };

  return (
    <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-surface shadow-card">
      <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 bg-[var(--coral)]">
        <Terminal size={16} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold uppercase tracking-wider text-ink-tertiary">
          {t("label")}
        </p>
        <code className="text-sm font-mono text-ink truncate block">
          {mcpEndpoint}
        </code>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={copyUrl}
          className="px-3 py-2 rounded-xl text-xs font-bold text-white bg-[var(--coral)] hover:opacity-90 transition-opacity flex items-center gap-1.5"
        >
          {copiedUrl ? <Check size={13} /> : <Copy size={13} />}
          {copiedUrl ? t("copied") : t("copyUrl")}
        </button>
        <button
          onClick={copyJson}
          className="px-3 py-2 rounded-xl text-xs font-bold text-ink border border-line-strong hover:border-terra hover:text-terra transition-all flex items-center gap-1.5"
        >
          {copiedJson ? <Check size={13} /> : <Braces size={13} />}
          {copiedJson ? t("copied") : t("copyJson")}
        </button>
      </div>
    </div>
  );
}
