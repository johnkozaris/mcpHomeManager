import { useRef, useEffect } from "react";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useScrollLock } from "@/hooks/useScrollLock";
import { Button } from "@/components/ui/Button";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "primary";
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmText,
  cancelText,
  variant = "primary",
  onConfirm,
  onCancel,
  isLoading = false,
}: Props) {
  const { t } = useTranslation("components", {
    keyPrefix: "ui.confirmDialog",
  });
  const dialogRef = useRef<HTMLDivElement>(null);
  const resolvedConfirmText = confirmText ?? t("confirm");
  const resolvedCancelText = cancelText ?? t("cancel");

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onCancel]);

  useFocusTrap(dialogRef, open);
  useScrollLock(open);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
        aria-hidden
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-desc"
        className="relative w-full max-w-sm bg-surface rounded-2xl border border-line shadow-elevated p-6 space-y-4"
      >
        <h2 id="confirm-title" className="text-lg font-semibold text-ink">
          {title}
        </h2>
        <p id="confirm-desc" className="text-sm text-ink-secondary">
          {description}
        </p>
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onCancel}
            disabled={isLoading}
          >
            {resolvedCancelText}
          </Button>
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            size="sm"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? t("working") : resolvedConfirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
