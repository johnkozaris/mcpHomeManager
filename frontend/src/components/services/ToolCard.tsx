import { useState } from "react";
import type { ToolDefinition } from "@/lib/types";
import { Toggle } from "@/components/ui/Toggle";
import { Badge } from "@/components/ui/Badge";
import { ServiceIconBadge } from "@/lib/service-meta";
import {
  ChevronDown,
  Pencil,
  X,
  Check,
  Zap,
  Settings2,
  Trash2,
} from "lucide-react";

interface SchemaProperty {
  type?: string;
  description?: string;
  default?: unknown;
  enum?: unknown[];
}

function ParameterSchema({ schema }: { schema: Record<string, unknown> }) {
  const properties = schema.properties as
    | Record<string, SchemaProperty>
    | undefined;
  const required = (schema.required as string[]) ?? [];

  if (!properties || Object.keys(properties).length === 0) {
    return <p className="text-xs text-ink-tertiary italic">No parameters</p>;
  }

  return (
    <div className="space-y-1.5">
      {Object.entries(properties).map(([name, prop]) => {
        const isRequired = required.includes(name);
        return (
          <div key={name} className="flex items-baseline gap-2 text-xs">
            <code className="font-mono text-terra shrink-0">{name}</code>
            {prop.type && (
              <span className="text-ink-tertiary shrink-0">{prop.type}</span>
            )}
            {isRequired ? (
              <Badge variant="brand">required</Badge>
            ) : (
              <Badge variant="default">optional</Badge>
            )}
            {prop.default !== undefined && (
              <span className="text-ink-tertiary shrink-0">
                = {JSON.stringify(prop.default)}
              </span>
            )}
            {prop.enum && (
              <span className="text-ink-tertiary shrink-0">
                [{prop.enum.map((v) => JSON.stringify(v)).join(", ")}]
              </span>
            )}
            {prop.description && (
              <span className="text-ink-secondary truncate">
                {prop.description}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function EditableParameterSchema({
  schema,
  descriptions,
  onDescriptionChange,
}: {
  schema: Record<string, unknown>;
  descriptions: Record<string, string>;
  onDescriptionChange: (paramName: string, value: string) => void;
}) {
  const properties = schema.properties as
    | Record<string, SchemaProperty>
    | undefined;
  const required = (schema.required as string[]) ?? [];

  if (!properties || Object.keys(properties).length === 0) {
    return <p className="text-xs text-ink-tertiary italic">No parameters</p>;
  }

  return (
    <div className="space-y-2.5">
      {Object.entries(properties).map(([name, prop]) => {
        const isRequired = required.includes(name);
        return (
          <div key={name} className="space-y-1">
            <div className="flex items-center gap-2 text-xs">
              <code className="font-mono text-terra shrink-0">{name}</code>
              {prop.type && (
                <span className="text-ink-tertiary shrink-0">{prop.type}</span>
              )}
              {isRequired ? (
                <Badge variant="brand">required</Badge>
              ) : (
                <Badge variant="default">optional</Badge>
              )}
            </div>
            <input
              type="text"
              value={descriptions[name] ?? prop.description ?? ""}
              onChange={(e) => onDescriptionChange(name, e.target.value)}
              placeholder="Parameter description (what the AI sees)…"
              className="w-full text-xs px-2.5 py-1.5 rounded-lg bg-surface border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all"
            />
          </div>
        );
      })}
    </div>
  );
}

interface ToolCardProps {
  tool: ToolDefinition;
  onToggle?: (toolName: string, enabled: boolean) => void;
  onSaveOverrides?: (
    toolName: string,
    descriptionOverride: string | null,
    parametersSchemaOverride: Record<string, unknown> | null,
  ) => void;
  showService?: boolean;
  onDelete?: (toolName: string) => void;
  onEditDefinition?: (toolName: string) => void;
  onTestTool?: (toolName: string) => void;
  testResult?: { success: boolean; message: string } | null;
  testingTool?: string | null;
}

const HINT_SEPARATOR = "\n\n[Hint] ";

function splitHint(description: string): { desc: string; hint: string } {
  const idx = description.indexOf(HINT_SEPARATOR);
  if (idx === -1) return { desc: description, hint: "" };
  return {
    desc: description.slice(0, idx),
    hint: description.slice(idx + HINT_SEPARATOR.length),
  };
}

function joinHint(desc: string, hint: string): string {
  const trimmedHint = hint.trim();
  if (!trimmedHint) return desc;
  return `${desc}${HINT_SEPARATOR}${trimmedHint}`;
}

export function ToolCard({
  tool,
  onToggle,
  onSaveOverrides,
  showService,
  onDelete,
  onEditDefinition,
  onTestTool,
  testResult,
  testingTool,
}: ToolCardProps) {
  // A tool is custom (user-defined) if it has http_method set
  const isCustomTool = tool.http_method != null;
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editDesc, setEditDesc] = useState("");
  const [editHint, setEditHint] = useState("");
  const [editParamDescs, setEditParamDescs] = useState<Record<string, string>>(
    {},
  );

  const schemaProps = tool.parameters_schema?.properties;
  const hasParams =
    schemaProps != null &&
    typeof schemaProps === "object" &&
    Object.keys(schemaProps as object).length > 0;
  const paramCount = hasParams ? Object.keys(schemaProps as object).length : 0;

  const startEditing = () => {
    const { desc, hint } = splitHint(tool.description);
    setEditDesc(desc);
    setEditHint(hint);
    const properties = tool.parameters_schema?.properties as
      | Record<string, SchemaProperty>
      | undefined;
    const paramDescs: Record<string, string> = {};
    if (properties) {
      for (const [name, prop] of Object.entries(properties)) {
        paramDescs[name] = prop.description ?? "";
      }
    }
    setEditParamDescs(paramDescs);
    setEditing(true);
    setExpanded(true);
  };

  const cancelEditing = () => setEditing(false);

  const saveEditing = () => {
    if (!onSaveOverrides) return;
    const combined = joinHint(editDesc.trim(), editHint);
    const descOverride = combined || null;
    const properties = tool.parameters_schema?.properties as
      | Record<string, SchemaProperty>
      | undefined;
    let schemaOverride: Record<string, unknown> | null = null;
    if (properties) {
      let hasChange = false;
      const newProperties: Record<string, SchemaProperty> = {};
      for (const [name, prop] of Object.entries(properties)) {
        const originalDesc = prop.description ?? "";
        const editedDesc = editParamDescs[name] ?? originalDesc;
        if (editedDesc !== originalDesc) hasChange = true;
        newProperties[name] = { ...prop, description: editedDesc || undefined };
      }
      if (hasChange) {
        schemaOverride = {
          ...tool.parameters_schema,
          properties: newProperties,
        };
      }
    }
    onSaveOverrides(tool.name, descOverride, schemaOverride);
    setEditing(false);
  };

  const isDisabled = !tool.is_enabled;

  return (
    <div
      className={`tool-card break-inside-avoid mb-3 ${isDisabled ? "opacity-50" : ""}`}
    >
      {/* Top color accent */}
      <div
        className={`h-1 rounded-t-2xl ${isDisabled ? "bg-ink-faint" : "bg-terra opacity-40"}`}
      />

      {/* Body */}
      <div className="p-4">
        {/* Name row */}
        <div className="flex items-center gap-2 mb-2">
          {showService && (
            <ServiceIconBadge type={tool.service_type} size="sm" />
          )}
          <code className="text-xs font-mono text-terra font-semibold truncate flex-1">
            {tool.name}
          </code>
          {tool.description_override && (
            <Badge variant="brand">customized</Badge>
          )}
        </div>

        {/* Description + hint */}
        {!editing &&
          (() => {
            const { desc, hint } = splitHint(tool.description);
            return (
              <div className="mb-3">
                <p className="text-sm text-ink-secondary leading-relaxed line-clamp-3">
                  {desc}
                </p>
                {hint && (
                  <p className="text-2xs text-clay mt-1.5 flex items-center gap-1">
                    <span className="font-semibold">Hint:</span> {hint}
                  </p>
                )}
              </div>
            );
          })()}

        {/* Controls row */}
        {!editing && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {hasParams && (
                <button
                  type="button"
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-2xs font-medium text-ink-tertiary hover:text-terra transition-colors"
                >
                  <ChevronDown
                    size={11}
                    className={`transition-transform ${expanded ? "rotate-180" : ""}`}
                  />
                  {paramCount} param{paramCount !== 1 ? "s" : ""}
                </button>
              )}
              {!hasParams && (
                <span className="text-2xs text-ink-faint">No params</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {isCustomTool && onTestTool && (
                <span className="inline-flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => onTestTool(tool.name)}
                    disabled={testingTool === tool.name}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-ink-secondary border border-line-strong hover:border-terra/50 hover:text-terra transition-all disabled:opacity-40"
                    title="Test endpoint reachability"
                    aria-label={`Test ${tool.name} endpoint`}
                  >
                    <Zap size={11} />
                    {testingTool === tool.name ? "Testing…" : "Test"}
                  </button>
                  {testResult && (
                    <span
                      className={`w-2 h-2 rounded-full ${testResult.success ? "bg-sage" : "bg-rust"}`}
                      title={testResult.message}
                      role="status"
                      aria-label={testResult.message}
                    />
                  )}
                </span>
              )}
              {isCustomTool && onEditDefinition && (
                <button
                  type="button"
                  onClick={() => onEditDefinition(tool.name)}
                  className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-ink-secondary border border-line-strong hover:border-terra/50 hover:text-terra transition-all"
                  title="Edit tool definition (method, path, schema)"
                  aria-label={`Edit ${tool.name} definition`}
                >
                  <Settings2 size={11} />
                </button>
              )}
              {isCustomTool && onDelete && (
                <button
                  type="button"
                  onClick={() => onDelete(tool.name)}
                  className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-ink-secondary border border-line-strong hover:border-rust/50 hover:text-rust transition-all"
                  title="Delete tool"
                  aria-label={`Delete ${tool.name}`}
                >
                  <Trash2 size={11} />
                </button>
              )}
              {onSaveOverrides && (
                <button
                  type="button"
                  onClick={startEditing}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-terra border border-terra/30 hover:bg-terra-bg hover:border-terra/50 transition-all"
                  title="Edit"
                >
                  <Pencil size={11} />
                  Edit
                </button>
              )}
              {onToggle ? (
                <Toggle
                  checked={tool.is_enabled}
                  onChange={(v) => onToggle(tool.name, v)}
                />
              ) : (
                <Badge variant={tool.is_enabled ? "positive" : "default"}>
                  {tool.is_enabled ? "enabled" : "disabled"}
                </Badge>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Editing mode */}
      {editing && (
        <div className="px-4 pb-4 space-y-3">
          <div>
            <label
              htmlFor={`desc-${tool.name}`}
              className="text-2xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1"
            >
              Tool description
            </label>
            <textarea
              id={`desc-${tool.name}`}
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              rows={3}
              className="w-full text-xs px-3 py-2 rounded-lg bg-canvas border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all resize-y"
              placeholder="Describe what this tool does (this is what the AI reads)…"
            />
          </div>
          <div>
            <label
              htmlFor={`hint-${tool.name}`}
              className="text-2xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1"
            >
              AI hint{" "}
              <span className="font-normal normal-case tracking-normal">
                (optional)
              </span>
            </label>
            <input
              id={`hint-${tool.name}`}
              type="text"
              value={editHint}
              onChange={(e) => setEditHint(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg bg-canvas border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all"
              placeholder="e.g. Call ha_list_entities first to discover valid entity IDs"
            />
            <p className="text-2xs text-ink-faint mt-1">
              Appended to the description so the AI knows when and how to use
              this tool.
            </p>
          </div>
          {hasParams && (
            <div>
              <span className="text-2xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1.5">
                Parameter descriptions
              </span>
              <EditableParameterSchema
                schema={tool.parameters_schema}
                descriptions={editParamDescs}
                onDescriptionChange={(name, value) =>
                  setEditParamDescs((prev) => ({ ...prev, [name]: value }))
                }
              />
            </div>
          )}
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={saveEditing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-terra text-white hover:opacity-90 transition-opacity"
            >
              <Check size={12} /> Save
            </button>
            <button
              type="button"
              onClick={cancelEditing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-ink-secondary hover:text-ink hover:bg-canvas-tertiary transition-all"
            >
              <X size={12} /> Cancel
            </button>
            {tool.description_override && (
              <button
                type="button"
                onClick={() => {
                  onSaveOverrides?.(tool.name, null, null);
                  setEditing(false);
                }}
                className="ml-auto text-2xs text-ink-tertiary hover:text-rust transition-colors"
              >
                Reset to original
              </button>
            )}
          </div>
        </div>
      )}

      {/* Expanded params */}
      {expanded && hasParams && !editing && (
        <div className="px-4 pb-4 pt-2 border-t border-line">
          <ParameterSchema schema={tool.parameters_schema} />
        </div>
      )}
    </div>
  );
}
