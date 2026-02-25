import { Component, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-canvas">
          <div className="max-w-sm text-center space-y-3">
            <p className="text-xl font-semibold text-ink">Something broke</p>
            <p className="text-sm text-ink-secondary">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Reload
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
