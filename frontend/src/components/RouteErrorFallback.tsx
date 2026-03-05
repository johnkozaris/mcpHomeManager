import {
  type ErrorComponentProps,
  Link,
  useRouter,
} from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { parseApiError } from "@/lib/utils";
import { useTranslation } from "react-i18next";

export function RouteErrorFallback({ error }: ErrorComponentProps) {
  const router = useRouter();
  const { t } = useTranslation("components", {
    keyPrefix: "routeErrorFallback",
  });

  const message = parseApiError(error, t("fallbackMessage"));

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="max-w-md w-full bg-surface border border-line rounded-xl p-8 text-center space-y-4 shadow-subtle">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rust-bg">
          <AlertTriangle className="h-6 w-6 text-rust" />
        </div>
        <h2 className="text-lg font-semibold text-ink">{t("title")}</h2>
        <p className="text-sm text-ink-secondary">{message}</p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => router.invalidate()}
          >
            {t("tryAgain")}
          </Button>
          <Link to="/">
            <Button variant="secondary" size="sm" type="button">
              {t("goHome")}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
