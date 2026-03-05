import { useState } from "react";
import { useServices } from "@/hooks/useServices";
import { api } from "@/lib/api";
import { ServiceCard } from "@/components/services/ServiceCard";
import { AddServicePanel } from "@/components/services/AddServicePanel";
import { ImportServiceModal } from "@/components/services/ImportServiceModal";
import { QueryState } from "@/components/ui/QueryState";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Server, Plus, Download, Upload, AlertCircle } from "lucide-react";

export function Services() {
  const { data: services, isLoading, isError, error } = useServices();
  const [modalOpen, setModalOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  async function handleExport() {
    setExportError(null);
    try {
      const yaml = await api.services.exportYaml();
      const blob = new Blob([yaml], { type: "application/x-yaml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "mcp-services.yaml";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError("Export failed. Please try again.");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">Services</h1>
          <p className="page-description">
            Your homelab apps connected through MCP
          </p>
        </div>
        <div className="flex items-center gap-2">
          {services && services.length > 0 && (
            <>
              <Button variant="secondary" size="sm" onClick={handleExport}>
                <Download size={14} />
                Export
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setImportOpen(true)}
              >
                <Upload size={14} />
                Import
              </Button>
            </>
          )}
          <Button size="sm" onClick={() => setModalOpen(true)}>
            <Plus size={14} />
            Connect Service
          </Button>
        </div>
      </div>

      {exportError && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-rust-bg border border-rust text-sm text-rust">
          <AlertCircle size={14} />
          {exportError}
        </div>
      )}

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage="Loading services…"
        errorMessage="Cannot reach the backend."
      >
        {services && services.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((svc) => (
              <ServiceCard key={svc.id} service={svc} />
            ))}
            <button
              onClick={() => setModalOpen(true)}
              className="card flex flex-col items-center justify-center min-h-[160px] border-2 border-dashed border-line-strong hover:border-terra/40 text-ink-tertiary hover:text-ink transition-all cursor-pointer"
            >
              <Plus size={28} className="mb-2" />
              <p className="text-sm font-medium">Connect Service</p>
              <p className="text-xs mt-0.5 text-ink-faint">
                Add a new homelab service
              </p>
            </button>
          </div>
        ) : (
          <EmptyState
            icon={Server}
            title="No services connected yet"
            description="Connect your first homelab service to start exposing MCP tools to AI agents."
          >
            <Button onClick={() => setModalOpen(true)}>
              <Plus size={14} />
              Connect Service
            </Button>
          </EmptyState>
        )}
      </QueryState>

      <AddServicePanel open={modalOpen} onClose={() => setModalOpen(false)} />
      <ImportServiceModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
      />
    </div>
  );
}
