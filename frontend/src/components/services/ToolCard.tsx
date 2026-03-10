import { useState } from "react";
import type { TestResult, ToolDefinition } from "@/lib/types";
import { Toggle } from "@/components/ui/Toggle";
import { Badge } from "@/components/ui/Badge";
import { ServiceIconBadge } from "@/lib/service-meta";
import { resolveBackendMessage } from "@/lib/utils";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation("components", {
    keyPrefix: "services.toolCard",
  });
  const properties = schema.properties as
    | Record<string, SchemaProperty>
    | undefined;
  const required = (schema.required as string[]) ?? [];

  if (!properties || Object.keys(properties).length === 0) {
    return (
      <p className="text-xs text-ink-tertiary italic">{t("noParameters")}</p>
    );
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
              <Badge variant="brand">{t("required")}</Badge>
            ) : (
              <Badge variant="default">{t("optional")}</Badge>
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
  const { t } = useTranslation("components", {
    keyPrefix: "services.toolCard",
  });
  const properties = schema.properties as
    | Record<string, SchemaProperty>
    | undefined;
  const required = (schema.required as string[]) ?? [];

  if (!properties || Object.keys(properties).length === 0) {
    return (
      <p className="text-xs text-ink-tertiary italic">{t("noParameters")}</p>
    );
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
                <Badge variant="brand">{t("required")}</Badge>
              ) : (
                <Badge variant="default">{t("optional")}</Badge>
              )}
            </div>
            <input
              type="text"
              value={descriptions[name] ?? prop.description ?? ""}
              onChange={(e) => onDescriptionChange(name, e.target.value)}
              placeholder={t("parameterDescriptionPlaceholder")}
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
  onToggle?: (tool: ToolDefinition, enabled: boolean) => void;
  onSaveOverrides?: (
    tool: ToolDefinition,
    descriptionOverride: string | null,
    parametersSchemaOverride: Record<string, unknown> | null,
    httpMethodOverride?: string | null,
    pathTemplateOverride?: string | null,
  ) => void;
  showService?: boolean;
  onDelete?: (toolName: string) => void;
  onEditDefinition?: (toolName: string) => void;
  onTestTool?: (toolName: string) => void;
  testResult?: TestResult | null;
  testingTool?: string | null;
  /** True when this is a user-created generic tool (not a built-in) */
  isGenericTool?: boolean;
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
  isGenericTool,
}: ToolCardProps) {
  const { t } = useTranslation("components", {
    keyPrefix: "services.toolCard",
  });
  // A tool is user-defined if the prop is set or the tool's own flag says so
  const isCustomTool = isGenericTool ?? tool.is_user_defined ?? false;
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editDesc, setEditDesc] = useState("");
  const [editHint, setEditHint] = useState("");
  const [editParamDescs, setEditParamDescs] = useState<Record<string, string>>(
    {},
  );
  const [editMethod, setEditMethod] = useState("");
  const [editPath, setEditPath] = useState("");

  const schemaProps = tool.parameters_schema?.properties;
  const hasParams =
    schemaProps != null &&
    typeof schemaProps === "object" &&
    Object.keys(schemaProps as object).length > 0;
  const paramCount = hasParams ? Object.keys(schemaProps as object).length : 0;
  const resolvedTestMessage = testResult
    ? resolveBackendMessage(testResult, {
        fallback: testResult.message,
        includeRawDetail: true,
      })
    : null;

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
    setEditMethod(tool.http_method_override ?? tool.http_method ?? "");
    setEditPath(tool.path_template_override ?? tool.path_template ?? "");
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

    // Compute endpoint overrides — null means "use the default"
    const origMethod = tool.http_method ?? "";
    const origPath = tool.path_template ?? "";
    const methodOverride = editMethod !== origMethod ? (editMethod || null) : null;
    const pathOverride = editPath !== origPath ? (editPath || null) : null;

    onSaveOverrides(tool, descOverride, schemaOverride, methodOverride, pathOverride);
    setEditing(false);
  };

  const isDisabled = !tool.is_enabled;

  return (
    <div
      className={`tool-card break-inside-avoid mb-3 ${isDisabled ? "opacity-50" : ""}`}
    >
      <div
        className={`h-1 rounded-t-2xl ${isDisabled ? "bg-ink-faint" : "bg-terra opacity-40"}`}
      />

      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          {showService && (
            <ServiceIconBadge type={tool.service_type} size="sm" />
          )}
          <code className="text-xs font-mono text-terra font-semibold truncate flex-1">
            {tool.name}
          </code>
          {tool.description_override && (
            <Badge variant="brand">{t("customized")}</Badge>
          )}
        </div>

        {!editing &&
          (() => {
            const { desc, hint } = splitHint(tool.description);
            return (
              <div className="mb-3">
                <p className="text-sm text-ink-secondary leading-relaxed line-clamp-3">
                  {desc}
                </p>
                {hint && (
                  <p className="text-xs text-clay mt-1.5 flex items-center gap-1">
                    <span className="font-semibold">{t("hintLabel")}</span>{" "}
                    {hint}
                  </p>
                )}
              </div>
            );
          })()}

        {!editing && tool.http_method && tool.path_template && (
          <div className="flex items-center gap-1.5 mb-3">
            <Badge variant={tool.http_method_override || tool.path_template_override ? "brand" : "default"}>
              {tool.http_method_override ?? tool.http_method}
            </Badge>
            <code className="text-xs text-ink-tertiary font-mono truncate">
              {tool.path_template_override ?? tool.path_template}
            </code>
            {(tool.http_method_override || tool.path_template_override) && (
              <span className="text-xs text-clay">
                {t("customizedParenthetical")}
              </span>
            )}
          </div>
        )}

        {!editing && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {hasParams && (
                <button
                  type="button"
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs font-medium text-ink-tertiary hover:text-terra transition-colors"
                >
                  <ChevronDown
                    size={11}
                    className={`transition-transform ${expanded ? "rotate-180" : ""}`}
                  />
                  {t("paramsCount", { count: paramCount })}
                </button>
              )}
              {!hasParams && (
                <span className="text-xs text-ink-faint">{t("noParams")}</span>
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
                    title={t("testEndpointReachability")}
                    aria-label={t("testEndpointAria", { toolName: tool.name })}
                  >
                    <Zap size={11} />
                    {testingTool === tool.name ? t("testing") : t("test")}
                  </button>
                  {testResult && (
                    <span
                      className={`w-2 h-2 rounded-full ${testResult.success ? "bg-sage" : "bg-rust"}`}
                      title={resolvedTestMessage ?? testResult.message}
                      role="status"
                      aria-label={resolvedTestMessage ?? testResult.message}
                    />
                  )}
                </span>
              )}
              {isCustomTool && onEditDefinition && (
                <button
                  type="button"
                  onClick={() => onEditDefinition(tool.name)}
                  className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-ink-secondary border border-line-strong hover:border-terra/50 hover:text-terra transition-all"
                  title={t("editToolDefinition")}
                  aria-label={t("editToolDefinitionAria", {
                    toolName: tool.name,
                  })}
                >
                  <Settings2 size={11} />
                </button>
              )}
              {isCustomTool && onDelete && (
                <button
                  type="button"
                  onClick={() => onDelete(tool.name)}
                  className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-ink-secondary border border-line-strong hover:border-rust/50 hover:text-rust transition-all"
                  title={t("deleteTool")}
                  aria-label={t("deleteToolAria", { toolName: tool.name })}
                >
                  <Trash2 size={11} />
                </button>
              )}
              {onSaveOverrides && (
                <button
                  type="button"
                  onClick={startEditing}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-terra border border-terra/30 hover:bg-terra-bg hover:border-terra/50 transition-all"
                  title={t("edit")}
                >
                  <Pencil size={11} />
                  {t("edit")}
                </button>
              )}
              {onToggle ? (
                <Toggle
                  checked={tool.is_enabled}
                  onChange={(v) => onToggle(tool, v)}
                />
              ) : (
                <Badge variant={tool.is_enabled ? "positive" : "default"}>
                  {tool.is_enabled ? t("enabled") : t("disabled")}
                </Badge>
              )}
            </div>
          </div>
        )}
      </div>

      {editing && (
        <div className="px-4 pb-4 space-y-3">
          <div>
            <label
              htmlFor={`desc-${tool.name}`}
              className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1"
            >
              {t("toolDescriptionLabel")}
            </label>
            <textarea
              id={`desc-${tool.name}`}
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              rows={3}
              className="w-full text-xs px-3 py-2 rounded-lg bg-canvas border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all resize-y"
              placeholder={t("toolDescriptionPlaceholder")}
            />
          </div>
          <div>
            <label
              htmlFor={`hint-${tool.name}`}
              className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1"
            >
              {t("aiHintLabel")}{" "}
              <span className="font-normal normal-case tracking-normal">
                {t("optionalParenthetical")}
              </span>
            </label>
            <input
              id={`hint-${tool.name}`}
              type="text"
              value={editHint}
              onChange={(e) => setEditHint(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg bg-canvas border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all"
              placeholder={t("aiHintPlaceholder")}
            />
            <p className="text-xs text-ink-faint mt-1">
              {t("aiHintHelpText")}
            </p>
          </div>
          {tool.http_method && (
            <div>
              <span className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1.5">
                {t("endpointLabel")}
              </span>
              <div className="flex gap-2">
                <select
                  value={editMethod}
                  onChange={(e) => setEditMethod(e.target.value)}
                  className="text-xs px-2.5 py-2 rounded-lg bg-canvas border border-line-strong text-ink focus:outline-none focus:shadow-focus focus:border-transparent transition-all w-28 shrink-0"
                >
                  {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={editPath}
                  onChange={(e) => setEditPath(e.target.value)}
                  className="flex-1 text-xs font-mono px-3 py-2 rounded-lg bg-canvas border border-line-strong text-ink placeholder:text-ink-faint focus:outline-none focus:shadow-focus focus:border-transparent transition-all"
                  placeholder={t("endpointPathPlaceholder")}
                />
              </div>
              <p className="text-xs text-ink-faint mt-1">
                {t("endpointHelpPrefix")}{" "}
                <code className="text-terra">{"{param}"}</code>{" "}
                {t("endpointHelpSuffix")}
              </p>
            </div>
          )}
          {hasParams && (
            <div>
              <span className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider block mb-1.5">
                {t("parameterDescriptionsLabel")}
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
              <Check size={12} /> {t("save")}
            </button>
            <button
              type="button"
              onClick={cancelEditing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-ink-secondary hover:text-ink hover:bg-canvas-tertiary transition-all"
            >
              <X size={12} /> {t("cancel")}
            </button>
            {(tool.description_override || tool.parameters_schema_override || tool.http_method_override || tool.path_template_override) && (
                <button
                  type="button"
                  onClick={() => {
                    onSaveOverrides?.(tool, null, null, null, null);
                    setEditing(false);
                  }}
                  className="ml-auto text-xs text-ink-tertiary hover:text-rust transition-colors"
                >
                {t("resetToOriginal")}
              </button>
            )}
          </div>
        </div>
      )}

      {expanded && hasParams && !editing && (
        <div className="px-4 pb-4 pt-2 border-t border-line">
          <ParameterSchema schema={tool.parameters_schema} />
        </div>
      )}
    </div>
  );
}
