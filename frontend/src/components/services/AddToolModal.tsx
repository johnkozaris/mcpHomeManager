import { useEffect, useRef, useState } from "react";
import {
  useCreateGenericTool,
  useUpdateGenericTool,
} from "@/hooks/useServices";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useScrollLock } from "@/hooks/useScrollLock";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { MonacoEditor } from "@/components/ui/MonacoEditor";
import type { GenericToolDefinition } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  serviceId: string;
  editTool?: GenericToolDefinition | null;
}

export function AddToolModal({ open, onClose, serviceId, editTool }: Props) {
  const isEditMode = !!editTool;
  const [toolName, setToolName] = useState(editTool?.tool_name ?? "");
  const [description, setDescription] = useState(editTool?.description ?? "");
  const [httpMethod, setHttpMethod] = useState(editTool?.http_method ?? "GET");
  const [pathTemplate, setPathTemplate] = useState(
    editTool?.path_template ?? "",
  );
  const [paramsSchema, setParamsSchema] = useState(
    editTool ? JSON.stringify(editTool.params_schema, null, 2) : "{}",
  );
  const [jsonError, setJsonError] = useState<string | null>(null);
  const createTool = useCreateGenericTool();
  const updateTool = useUpdateGenericTool();
  const dialogRef = useRef<HTMLDivElement>(null);

  const mutation = isEditMode ? updateTool : createTool;
  const toolNameValid = !toolName || /^[a-zA-Z][a-zA-Z0-9_]*$/.test(toolName);

  useFocusTrap(dialogRef, open);
  useScrollLock(open);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = () => {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(paramsSchema);
    } catch {
      setJsonError("Invalid JSON in parameters schema");
      return;
    }
    setJsonError(null);

    if (isEditMode) {
      updateTool.mutate(
        {
          serviceId,
          toolName: editTool.tool_name,
          data: {
            description,
            http_method: httpMethod,
            path_template: pathTemplate,
            params_schema: parsed,
          },
        },
        { onSuccess: () => onClose() },
      );
    } else {
      createTool.mutate(
        {
          serviceId,
          data: {
            tool_name: toolName,
            description,
            http_method: httpMethod,
            path_template: pathTemplate,
            params_schema: parsed,
          },
        },
        {
          onSuccess: () => {
            setToolName("");
            setDescription("");
            setPathTemplate("");
            setParamsSchema("{}");
            onClose();
          },
        },
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-hidden
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-tool-title"
        aria-describedby="add-tool-desc"
        className="relative w-full max-w-lg bg-surface rounded-2xl border border-line shadow-elevated overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-line">
          <h2 id="add-tool-title" className="text-lg font-semibold text-ink">
            {isEditMode ? "Edit Tool Definition" : "Add Tool"}
          </h2>
          <button
            onClick={onClose}
            aria-label={
              isEditMode ? "Close edit tool dialog" : "Close add tool dialog"
            }
            className="text-ink-tertiary hover:text-ink transition-colors"
          >
            &times;
          </button>
        </div>
        <div className="p-6 space-y-3">
          <p id="add-tool-desc" className="sr-only">
            {isEditMode
              ? "Edit the definition of this MCP tool."
              : "Create a new MCP tool for this generic REST service."}
          </p>
          <Input
            label="Tool Name"
            placeholder="e.g. list_items"
            value={toolName}
            onChange={(e) => setToolName(e.target.value)}
            required
            disabled={isEditMode}
            error={
              !toolNameValid
                ? "Must start with a letter; only letters, numbers, and underscores"
                : undefined
            }
          />
          <Input
            label="Description"
            placeholder="List all items"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label
                htmlFor="http-method"
                className="block text-sm font-medium text-ink-secondary"
              >
                HTTP Method
              </label>
              <select
                id="http-method"
                value={httpMethod}
                onChange={(e) => setHttpMethod(e.target.value)}
                className="input-field"
              >
                {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Path Template"
              placeholder="/api/v1/items"
              value={pathTemplate}
              onChange={(e) => setPathTemplate(e.target.value)}
              required
            />
          </div>
          <div>
            <p className="section-label mb-2">Parameters Schema (JSON)</p>
            <MonacoEditor
              value={paramsSchema}
              onChange={setParamsSchema}
              language="json"
              height="120px"
            />
          </div>
          {(mutation.isError || jsonError) && (
            <p className="text-xs text-rust">
              {jsonError ??
                (mutation.error instanceof Error
                  ? mutation.error.message
                  : isEditMode
                    ? "Failed to update tool"
                    : "Failed to create tool")}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={
                mutation.isPending ||
                !toolName ||
                !pathTemplate ||
                !toolNameValid
              }
            >
              {mutation.isPending
                ? isEditMode
                  ? "Saving\u2026"
                  : "Creating\u2026"
                : isEditMode
                  ? "Save Changes"
                  : "Create Tool"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
