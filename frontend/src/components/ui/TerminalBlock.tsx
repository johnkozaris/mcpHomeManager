import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import { useTranslation } from "react-i18next";

interface Props {
  code: string;
  label?: string;
}

export function TerminalBlock({ code, label }: Props) {
  const { t } = useTranslation("components", { keyPrefix: "ui.terminalBlock" });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(id);
  }, [copied]);

  function handleCopy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
  }

  return (
    <div className="rounded-xl overflow-hidden border border-[var(--terminal-border)]">
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ backgroundColor: "var(--terminal-title)" }}
      >
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "var(--terminal-dot-red)" }}
            />
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "var(--terminal-dot-yellow)" }}
            />
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: "var(--terminal-dot-green)" }}
            />
          </div>
          {label && (
            <span
              className="text-xs font-medium ml-2"
              style={{ color: "var(--terminal-label)" }}
            >
              {label}
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs transition-colors hover:text-white focus-visible:outline-none focus-visible:shadow-focus rounded"
          style={{ color: "var(--terminal-label)" }}
          aria-label={t("copyToClipboard")}
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? t("copied") : t("copy")}
        </button>
      </div>

      <pre
        className="px-4 py-4 text-sm font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap select-all"
        style={{
          backgroundColor: "var(--terminal-bg)",
          color: "var(--terminal-text)",
        }}
      >
        {code}
      </pre>
    </div>
  );
}
