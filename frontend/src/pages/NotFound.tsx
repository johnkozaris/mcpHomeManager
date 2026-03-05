import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import { ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

export function NotFound() {
  const { t } = useTranslation("notFound");

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-4">
        <p className="text-6xl font-bold text-ink-faint">404</p>
        <p className="text-lg font-medium text-ink">{t("title")}</p>
        <p className="text-sm text-ink-secondary">{t("description")}</p>
        <div className="pt-2">
          <Link to="/">
            <Button variant="secondary" size="sm">
              <ArrowLeft size={14} />
              {t("backToHome")}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
