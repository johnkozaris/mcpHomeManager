import { useEffect, useRef, useState } from "react";
import { useImportOpenapi } from "@/hooks/useServices";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useScrollLock } from "@/hooks/useScrollLock";
import { Button } from "@/components/ui/Button";
import { MonacoEditor } from "@/components/ui/MonacoEditor";
import type { OpenAPIImportResult } from "@/lib/types";
import { parseApiError } from "@/lib/utils";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  onClose: () => void;
  serviceId: string;
}

export function ImportOpenAPIModal({ open, onClose, serviceId }: Props) {
  const { t } = useTranslation("components", {
    keyPrefix: "services.importOpenApiModal",
  });
  const [spec, setSpec] = useState("");
  const [importResult, setImportResult] = useState<OpenAPIImportResult | null>(
    null,
  );
  const importOpenapi = useImportOpenapi();
  const dialogRef = useRef<HTMLDivElement>(null);

  useFocusTrap(dialogRef, open);
  useScrollLock(open);

  const handleClose = () => {
    setImportResult(null);
    setSpec("");
    onClose();
  };

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

  const importedCount = importResult?.imported.length ?? 0;
  const skippedCount = importResult?.skipped.length ?? 0;
  const allSkipped =
    importResult !== null && importedCount === 0 && skippedCount > 0;
  const hasSkipped =
    importResult !== null && skippedCount > 0 && importedCount > 0;
  const allImported =
    importResult !== null && importedCount > 0 && skippedCount === 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={handleClose}
        aria-hidden
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-openapi-title"
        aria-describedby="import-openapi-desc"
        className="relative w-full max-w-lg bg-surface rounded-2xl border border-line shadow-elevated overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-line">
          <h2
            id="import-openapi-title"
            className="text-lg font-semibold text-ink"
          >
            {t("title")}
          </h2>
          <button
            onClick={handleClose}
            aria-label={t("closeDialog")}
            className="text-ink-tertiary hover:text-ink transition-colors"
          >
            &times;
          </button>
        </div>
        <div className="p-6 space-y-4">
          {importResult ? (
            <>
              {allImported && (
                <p className="text-sm font-medium text-sage">
                  {t("importedSummary", { count: importedCount })}
                </p>
              )}
              {hasSkipped && (
                <p className="text-sm font-medium text-clay">
                  {t("partialSummary", {
                    importedCount,
                    skippedCount,
                  })}
                </p>
              )}
              {allSkipped && (
                <p className="text-sm font-medium text-clay">
                  {t("allSkippedSummary", { count: skippedCount })}
                </p>
              )}
              <div className="flex justify-end">
                <Button onClick={handleClose}>{t("ok")}</Button>
              </div>
            </>
          ) : (
            <>
              <p
                id="import-openapi-desc"
                className="text-sm text-ink-secondary"
              >
                {t("description")}
              </p>
              <MonacoEditor
                value={spec}
                onChange={setSpec}
                language={spec.trimStart().startsWith("{") ? "json" : "yaml"}
                height="300px"
              />
              {importOpenapi.isError && (
                <p className="text-xs text-rust">
                  {parseApiError(importOpenapi.error, t("importFailed"))}
                </p>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={handleClose}>
                  {t("cancel")}
                </Button>
                <Button
                  onClick={() => {
                    importOpenapi.mutate(
                      { serviceId, spec },
                      {
                        onSuccess: (result) => {
                          setSpec("");
                          if (
                            result.imported.length > 0 &&
                            result.skipped.length === 0
                          ) {
                            setImportResult(result);
                            setTimeout(() => {
                              setImportResult(null);
                              onClose();
                            }, 1500);
                          } else {
                            setImportResult(result);
                          }
                        },
                      },
                    );
                  }}
                  disabled={importOpenapi.isPending || !spec.trim()}
                >
                  {importOpenapi.isPending ? t("importing") : t("import")}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
