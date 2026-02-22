import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import { ArrowLeft } from "lucide-react";

export function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-4">
        <p className="text-6xl font-bold text-ink-faint">404</p>
        <p className="text-lg font-medium text-ink">Page not found</p>
        <p className="text-sm text-ink-secondary">
          This page doesn't exist or has been moved.
        </p>
        <div className="pt-2">
          <Link to="/">
            <Button variant="secondary" size="sm">
              <ArrowLeft size={14} />
              Back to home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
