import {
  type ErrorComponentProps,
  Link,
  useRouter,
} from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function RouteErrorFallback({ error }: ErrorComponentProps) {
  const router = useRouter();

  const message =
    error instanceof Error ? error.message : "An unexpected error occurred.";

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="max-w-md w-full bg-surface border border-line rounded-xl p-8 text-center space-y-4 shadow-subtle">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rust-bg">
          <AlertTriangle className="h-6 w-6 text-rust" />
        </div>
        <h2 className="text-lg font-semibold text-ink">Something went wrong</h2>
        <p className="text-sm text-ink-secondary">{message}</p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => router.invalidate()}
          >
            Try again
          </Button>
          <Link to="/">
            <Button variant="secondary" size="sm" type="button">
              Go home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
