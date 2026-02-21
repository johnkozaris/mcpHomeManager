import type { ReactNode } from "react";

interface QueryStateProps {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  loadingMessage?: string;
  errorMessage?: string;
  children: ReactNode;
}

export function QueryState({
  isLoading,
  isError,
  error,
  loadingMessage = "Loading…",
  errorMessage,
  children,
}: QueryStateProps) {
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
      ? "Authentication required — sign in again to continue."
      : isNetworkError
        ? "Could not reach the server. Is the backend running?"
        : raw || errorMessage || "Something went wrong";
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
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-line-strong border-t-terra rounded-full animate-spin" />
          <span className="text-sm text-ink-tertiary">{loadingMessage}</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
