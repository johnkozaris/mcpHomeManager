import { Eye } from "lucide-react";
import { Button } from "@/components/ui/Button";
import type { AppDefinition } from "@/lib/types";
import { useTranslation } from "react-i18next";

interface Props {
  app: AppDefinition;
  onPreview: (app: AppDefinition) => void;
}

export function AppCard({ app, onPreview }: Props) {
  const { t } = useTranslation("components", { keyPrefix: "services.appCard" });

  return (
    <div className="flex items-center justify-between p-3 rounded-xl border border-line">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-ink">{app.title}</p>
        <p className="text-2xs text-ink-tertiary truncate">{app.description}</p>
      </div>
      <Button variant="secondary" size="sm" onClick={() => onPreview(app)}>
        <Eye size={14} />
        {t("preview")}
      </Button>
    </div>
  );
}
