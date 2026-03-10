import { useState, useEffect, useRef } from "react";
import { X, Search, ChevronLeft } from "lucide-react";
import {
  useDiscoverServices,
  useCreateService,
  useTestConnection,
} from "@/hooks/useServices";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useScrollLock } from "@/hooks/useScrollLock";
import { ServiceConfig } from "@/components/services/ServiceConfig";
import {
  ServiceIconBadge,
  SERVICE_META,
  getServiceMeta,
} from "@/lib/service-meta";
import { BUILTIN_SERVICE_TYPES } from "@/lib/types";
import { parseApiError } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useNavigate } from "@tanstack/react-router";
import type { ServiceType, DiscoveredService } from "@/lib/types";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface PrefillData {
  name: string;
  displayName: string;
  type: ServiceType;
  baseUrl: string;
}

/* ─── Catalog grid ──────────────────────────────────────────── */

function CatalogGrid({ onSelect }: { onSelect: (type: ServiceType) => void }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {BUILTIN_SERVICE_TYPES.map((type) => {
        const meta = SERVICE_META[type];
        return (
          <button
            key={type}
            onClick={() => onSelect(type)}
            className="flex items-center gap-3 p-3 rounded-xl border border-line hover:border-line-strong hover:bg-surface-hover transition-all text-left group"
          >
            <ServiceIconBadge type={type} size="sm" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-ink group-hover:text-terra transition-colors">
                {meta.label}
              </p>
              <p className="text-xs text-ink-tertiary truncate">
                {meta.description}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
}

/* ─── Auto-detect section ──────────────────────────────────── */

function ScanSection({
  onSelectService,
}: {
  onSelectService: (svc: DiscoveredService) => void;
}) {
  const discoverServices = useDiscoverServices();
  const { t } = useTranslation("components", {
    keyPrefix: "services.addServicePanel",
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink-secondary">
          {t("scanDescription")}
        </p>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => discoverServices.mutate()}
          disabled={discoverServices.isPending}
        >
          <Search size={14} />
          {discoverServices.isPending ? t("scanning") : t("scan")}
        </Button>
      </div>

      {discoverServices.data && discoverServices.data.length > 0 && (
        <div className="space-y-2">
          {discoverServices.data.map((svc: DiscoveredService) => {
            const meta = getServiceMeta(svc.service_type);
            return (
              <button
                key={svc.container_name}
                onClick={() => onSelectService(svc)}
                className="w-full flex items-center gap-3 p-3 rounded-xl border border-line hover:border-line-strong hover:bg-surface-hover transition-all text-left group"
              >
                <ServiceIconBadge type={svc.service_type} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-ink group-hover:text-terra transition-colors">
                    {svc.display_name}
                  </p>
                  <p className="text-xs text-ink-tertiary font-mono truncate">
                    {svc.suggested_url}
                  </p>
                </div>
                <Badge>{meta.label}</Badge>
              </button>
            );
          })}
        </div>
      )}

      {discoverServices.data && discoverServices.data.length === 0 && (
        <p className="text-sm text-ink-tertiary text-center py-6">
          {t("noKnownServices")}
        </p>
      )}
    </div>
  );
}

/* ─── Modal ─────────────────────────────────────────────────── */

export function AddServicePanel({ open, onClose }: Props) {
  const { t } = useTranslation("components", {
    keyPrefix: "services.addServicePanel",
  });
  const [selectedType, setSelectedType] = useState<ServiceType | null>(null);
  const [prefill, setPrefill] = useState<PrefillData | null>(null);
  const createService = useCreateService();
  const testConnection = useTestConnection();
  const navigate = useNavigate();
  const [mutationError, setMutationError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleClose = () => {
    setSelectedType(null);
    setPrefill(null);
    setMutationError(null);
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

  function handleSelectFromCatalog(type: ServiceType) {
    setSelectedType(type);
    setPrefill(null);
  }

  function handleSelectFromScan(svc: DiscoveredService) {
    setSelectedType(svc.service_type);
    setPrefill({
      name: svc.container_name,
      displayName: svc.display_name,
      type: svc.service_type,
      baseUrl: svc.suggested_url,
    });
  }

  function handleBack() {
    setSelectedType(null);
    setPrefill(null);
    setMutationError(null);
  }

  if (!open) return null;

  const headerLabel = selectedType
    ? t("connectWithLabel", { label: getServiceMeta(selectedType).label })
    : t("connectService");
  const headerId = "add-service-title";

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
        aria-labelledby={headerId}
        className="relative w-full max-w-lg bg-surface rounded-2xl border border-line shadow-elevated overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-line">
          <div className="flex items-center gap-3">
            {selectedType && (
              <button
                onClick={handleBack}
                className="text-ink-tertiary hover:text-ink transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
            )}
            <h2 id={headerId} className="text-lg font-semibold text-ink">
              {headerLabel}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-ink-tertiary hover:text-ink transition-colors"
            aria-label={t("closeDialog")}
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto space-y-6">
          {mutationError && (
            <div
              role="alert"
              className="flex items-center gap-3 p-3 rounded-lg bg-rust-bg border border-rust"
            >
              <span className="text-sm text-rust flex-1">{mutationError}</span>
              <button
                className="text-xs text-rust hover:underline"
                onClick={() => setMutationError(null)}
              >
                {t("dismiss")}
              </button>
            </div>
          )}

          {selectedType ? (
            <ServiceConfig
              initialType={selectedType}
              prefill={prefill ?? undefined}
              onSubmit={(data) => {
                setMutationError(null);
                createService.mutate(data, {
                  onSuccess: (created) => {
                    handleClose();
                    testConnection.mutate(created.id);
                    navigate({
                      to: "/services/$id",
                      params: { id: created.id },
                    });
                  },
                  onError: (err) =>
                    setMutationError(
                      parseApiError(err, t("failedConnectService")),
                    ),
                });
              }}
              isLoading={createService.isPending}
            />
          ) : (
            <>
              <div>
                <h3 className="section-label mb-3">{t("chooseService")}</h3>
                <CatalogGrid onSelect={handleSelectFromCatalog} />
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 border-t border-line" />
                <span className="text-xs text-ink-tertiary">{t("or")}</span>
                <div className="flex-1 border-t border-line" />
              </div>

              <div>
                <h3 className="section-label mb-3">{t("autoDetect")}</h3>
                <ScanSection onSelectService={handleSelectFromScan} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
