import { useState } from "react";
import { Link } from "@tanstack/react-router";
import type { ToolDefinition } from "@/lib/types";
import { ToolCard } from "@/components/services/ToolCard";
import { LayoutGrid, ArrowRight, Code2, Wrench } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";

interface Props {
  tools: ToolDefinition[];
  /** All tools including disabled — used when we want to show disabled tools greyed out. */
  allTools?: ToolDefinition[];
  onToggle?: (tool: ToolDefinition, enabled: boolean) => void;
  onSaveOverrides?: (
    tool: ToolDefinition,
    descriptionOverride: string | null,
    parametersSchemaOverride: Record<string, unknown> | null,
    httpMethodOverride?: string | null,
    pathTemplateOverride?: string | null,
  ) => void;
  showService?: boolean;
  showJsonView?: boolean;
  onDelete?: (toolName: string) => void;
  onEditDefinition?: (toolName: string) => void;
  onTestTool?: (toolName: string) => void;
  testResults?: Record<string, { success: boolean; message: string }>;
  testingTool?: string | null;
}

function JsonView({ tools }: { tools: ToolDefinition[] }) {
  const json = tools.map((t) => ({
    name: t.name,
    description: t.description,
    parameters: t.parameters_schema,
    enabled: t.is_enabled,
    ...(t.description_override
      ? { description_override: t.description_override }
      : {}),
  }));

  return (
    <div className="rounded-xl bg-[var(--terminal-bg)] border border-[var(--terminal-border)] overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-[var(--terminal-title)] border-b border-[var(--terminal-border)]">
        <Code2 size={13} className="text-[var(--terminal-label)]" />
        <span className="text-xs font-medium text-[var(--terminal-label)]">
          tools.json
        </span>
      </div>
      <pre className="p-4 text-xs font-mono text-[var(--terminal-text)] overflow-x-auto max-h-[600px] overflow-y-auto leading-relaxed">
        {JSON.stringify(json, null, 2)}
      </pre>
    </div>
  );
}

export function ToolList({
  tools,
  allTools,
  onToggle,
  onSaveOverrides,
  showService = false,
  showJsonView = false,
  onDelete,
  onEditDefinition,
  onTestTool,
  testResults,
  testingTool,
}: Props) {
  const [viewMode, setViewMode] = useState<"cards" | "json">("cards");
  const displayTools = allTools ?? tools;

  if (displayTools.length === 0) {
    return (
      <EmptyState
        icon={Wrench}
        title="No tools registered"
        description="Tools will appear here once a service is connected."
      />
    );
  }

  return (
    <div className="space-y-3">
      {showJsonView && (
        <div className="flex items-center">
          <div className="inline-flex rounded-lg border border-line-strong overflow-hidden">
            <button
              onClick={() => setViewMode("cards")}
              className={`p-2 transition-all ${viewMode === "cards" ? "bg-terra text-white" : "bg-surface text-ink-tertiary hover:text-ink hover:bg-surface-hover"}`}
              title="Card view"
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setViewMode("json")}
              className={`p-2 border-l border-line-strong transition-all ${viewMode === "json" ? "bg-terra text-white" : "bg-surface text-ink-tertiary hover:text-ink hover:bg-surface-hover"}`}
              title="JSON view"
            >
              <Code2 size={14} />
            </button>
          </div>
        </div>
      )}

      {viewMode === "json" ? (
        <JsonView tools={displayTools} />
      ) : (
        <>
          <div style={{ columnCount: 3, columnGap: "0.75rem" }}>
            {displayTools.map((tool) => (
              <ToolCard
                key={tool.name}
                tool={tool}
                onToggle={onToggle}
                onSaveOverrides={onSaveOverrides}
                showService={showService}
                onDelete={onDelete}
                onEditDefinition={onEditDefinition}
                onTestTool={onTestTool}
                testResult={testResults?.[tool.name] ?? null}
                testingTool={testingTool}
              />
            ))}
          </div>

          {!onToggle && displayTools.length > 0 && (
            <div className="pt-3 border-t border-line">
              <Link
                to="/tools"
                className="flex items-center gap-1.5 text-xs text-terra hover:text-terra-light transition-colors"
              >
                Manage tool access on the Tools page
                <ArrowRight size={12} />
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  );
}
