import { useState, useRef, useEffect } from "react";
import { X, Upload, FileText } from "lucide-react";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useScrollLock } from "@/hooks/useScrollLock";
import { useImportServices } from "@/hooks/useServices";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ParsedService {
  name: string;
  service_type: string;
  base_url: string;
}

function parseYamlNames(content: string): ParsedService[] {
  // Simple extraction of service names from YAML — no full parser needed in browser
  const services: ParsedService[] = [];
  const lines = content.split("\n");
  let current: Partial<ParsedService> = {};

  for (const line of lines) {
    const nameMatch = line.match(/^\s*-?\s*name:\s*(.+)/);
    if (nameMatch?.[1]) {
      if (current.name) services.push(current as ParsedService);
      current = { name: nameMatch[1].trim().replace(/^["']|["']$/g, "") };
    }
    const typeMatch = line.match(/^\s*service_type:\s*(.+)/);
    if (typeMatch?.[1])
      current.service_type = typeMatch[1].trim().replace(/^["']|["']$/g, "");
    const urlMatch = line.match(/^\s*base_url:\s*(.+)/);
    if (urlMatch?.[1])
      current.base_url = urlMatch[1].trim().replace(/^["']|["']$/g, "");
  }
  if (current.name) services.push(current as ParsedService);
  return services;
}

export function ImportServiceModal({ open, onClose }: Props) {
  const [yamlContent, setYamlContent] = useState("");
  const [parsed, setParsed] = useState<ParsedService[]>([]);
  const [tokens, setTokens] = useState<Record<string, string>>({});
  const importServices = useImportServices();
  const modalRef = useRef<HTMLDivElement>(null);

  const handleClose = () => {
    setYamlContent("");
    setParsed([]);
    setTokens({});
    onClose();
  };

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  useFocusTrap(modalRef, open);
  useScrollLock(open);

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result;
      if (typeof content !== "string") return;
      setYamlContent(content);
      setParsed(parseYamlNames(content));
    };
    reader.onerror = () => {
      setYamlContent("");
      setParsed([]);
    };
    reader.readAsText(file);
  }

  function handleImport() {
    importServices.mutate(
      { yamlContent, tokenMap: tokens },
      { onSuccess: () => handleClose() },
    );
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={handleClose}
        aria-hidden
      />
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-title"
        className="relative w-full max-w-lg bg-surface rounded-2xl border border-line shadow-elevated overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-line">
          <h2 id="import-title" className="text-lg font-semibold text-ink">
            Import Services
          </h2>
          <button
            onClick={handleClose}
            className="text-ink-tertiary hover:text-ink transition-colors"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto space-y-4">
          <div>
            <span className="section-label mb-2 block">YAML Config File</span>
            <label className="flex items-center gap-3 p-4 rounded-xl border-2 border-dashed border-line hover:border-terra cursor-pointer transition-colors">
              <Upload size={20} className="text-ink-tertiary" />
              <span className="text-sm text-ink-secondary">
                {yamlContent ? "File loaded" : "Choose a .yml file"}
              </span>
              <input
                type="file"
                accept=".yml,.yaml"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>
          </div>

          {parsed.length > 0 && (
            <div className="space-y-3">
              <p className="section-label">Services found ({parsed.length})</p>
              {parsed.map((svc) => (
                <div
                  key={svc.name}
                  className="p-3 rounded-xl border border-line space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <FileText size={14} className="text-ink-tertiary" />
                    <span className="text-sm font-medium text-ink">
                      {svc.name}
                    </span>
                    <Badge>{svc.service_type}</Badge>
                  </div>
                  <p className="text-xs text-ink-tertiary font-mono">
                    {svc.base_url}
                  </p>
                  <Input
                    label="API Token"
                    type="password"
                    placeholder="Enter API token for this service"
                    value={tokens[svc.name] || ""}
                    onChange={(e) =>
                      setTokens((prev) => ({
                        ...prev,
                        [svc.name]: e.target.value,
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          )}

          {importServices.data && (
            <div className="space-y-1 text-sm">
              {importServices.data.created.length > 0 && (
                <p className="text-sage">
                  Created: {importServices.data.created.join(", ")}
                </p>
              )}
              {importServices.data.skipped.length > 0 && (
                <p className="text-clay">
                  Skipped: {importServices.data.skipped.join(", ")}
                </p>
              )}
              {importServices.data.errors.length > 0 && (
                <p className="text-rust">
                  Errors: {importServices.data.errors.join("; ")}
                </p>
              )}
            </div>
          )}

          {importServices.error && (
            <p className="text-sm text-rust">
              {importServices.error instanceof Error
                ? importServices.error.message
                : "Import failed"}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleImport}
              disabled={
                !yamlContent || parsed.length === 0 || importServices.isPending
              }
            >
              {importServices.isPending ? "Importing…" : "Import"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
