import { Component, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { type WithTranslation, withTranslation } from "react-i18next";

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  error: Error | null;
}

type ErrorBoundaryProps = Props & WithTranslation;

class ErrorBoundaryBase extends Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    const { t } = this.props;

    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-canvas">
          <div className="max-w-sm text-center space-y-3">
            <p className="text-xl font-semibold text-ink">
              {t("errorBoundary.title", { ns: "components" })}
            </p>
            <p className="text-sm text-ink-secondary">
              {this.state.error?.message ||
                t("errorBoundary.fallbackMessage", { ns: "components" })}
            </p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.location.reload()}
            >
              {t("errorBoundary.reload", { ns: "components" })}
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export const ErrorBoundary = withTranslation("components")(ErrorBoundaryBase);
