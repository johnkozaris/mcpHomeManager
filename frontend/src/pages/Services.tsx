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
import { Skeleton } from "@/components/ui/Skeleton";
import { useTranslation } from "react-i18next";

function ServicesSkeleton() {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }, (_, i) => (
        <Skeleton key={i} className="h-[160px]" />
      ))}
    </div>
  );
}

export function Services() {
  const { t } = useTranslation("services", { keyPrefix: "listPage" });
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
      setExportError(t("errors.exportFailed"));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">{t("title")}</h1>
          <p className="page-description">{t("description")}</p>
        </div>
        <div className="flex items-center gap-2">
          {services && services.length > 0 && (
            <>
              <Button variant="secondary" size="sm" onClick={handleExport}>
                <Download size={14} />
                {t("actions.export")}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setImportOpen(true)}
              >
                <Upload size={14} />
                {t("actions.import")}
              </Button>
            </>
          )}
          <Button size="sm" onClick={() => setModalOpen(true)}>
            <Plus size={14} />
            {t("actions.connectService")}
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
        loadingMessage={t("query.loading")}
        errorMessage={t("query.error")}
        skeleton={<ServicesSkeleton />}
      >
        {services && services.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((svc) => (
              <ServiceCard key={svc.id} service={svc} />
            ))}
            <button
              onClick={() => setModalOpen(true)}
              className="card flex flex-col items-center justify-center min-h-[160px] border-2 border-dashed border-line-strong hover:border-terra/40 text-ink-tertiary hover:text-ink transition-all cursor-pointer"
            >
              <Plus size={28} className="mb-2" />
              <p className="text-sm font-medium">{t("actions.connectService")}</p>
              <p className="text-xs mt-0.5 text-ink-faint">
                {t("cards.connectDescription")}
              </p>
            </button>
          </div>
        ) : (
          <EmptyState
            icon={Server}
            title={t("empty.title")}
            description={t("empty.description")}
          >
            <Button onClick={() => setModalOpen(true)}>
              <Plus size={14} />
              {t("actions.connectService")}
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
