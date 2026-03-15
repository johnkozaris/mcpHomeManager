import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { parseApiError } from "@/lib/utils";

interface QueryStateProps {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  loadingMessage?: string;
  errorMessage?: string;
  skeleton?: ReactNode;
  children: ReactNode;
}

export function QueryState({
  isLoading,
  isError,
  error,
  loadingMessage,
  errorMessage,
  skeleton,
  children,
}: QueryStateProps) {
  const { t } = useTranslation("errors");
  const resolvedLoadingMessage = loadingMessage ?? t("queryState.loading");

  if (isError) {
    const is401 =
      error instanceof Error &&
      (error.name === "UnauthorizedError" || error.message.startsWith("401:"));
    const raw = error instanceof Error ? error.message : null;
    const isNetworkError =
      raw?.includes("Failed to fetch") ||
      raw?.includes("NetworkError") ||
      raw?.includes("fetch");
    const msg = is401
      ? t("queryState.authRequired")
      : isNetworkError
        ? t("queryState.networkUnreachable")
        : parseApiError(error, errorMessage || t("queryState.generic"));
    return (
      <div
        className={`flex items-center gap-3 py-6 px-5 rounded-xl ${is401 ? "bg-clay-bg border border-clay" : "bg-rust-bg border border-rust"}`}
      >
        <div
          className={`w-2 h-2 rounded-full ${is401 ? "bg-clay" : "bg-rust"} shrink-0`}
        />
        <p className={`text-sm ${is401 ? "text-clay" : "text-rust"}`}>{msg}</p>
      </div>
    );
  }

  if (isLoading) {
    if (skeleton) return <>{skeleton}</>;
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-line-strong border-t-terra rounded-full animate-spin" />
          <span className="text-sm text-ink-tertiary">
            {resolvedLoadingMessage}
          </span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
