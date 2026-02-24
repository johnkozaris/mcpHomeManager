import { Eye } from "lucide-react";
import { Button } from "@/components/ui/Button";
import type { AppDefinition } from "@/lib/types";

interface Props {
  app: AppDefinition;
  onPreview: (app: AppDefinition) => void;
}

export function AppCard({ app, onPreview }: Props) {
  return (
    <div className="flex items-center justify-between p-3 rounded-xl border border-line">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-ink">{app.title}</p>
        <p className="text-2xs text-ink-tertiary truncate">{app.description}</p>
      </div>
      <Button variant="secondary" size="sm" onClick={() => onPreview(app)}>
        <Eye size={14} />
        Preview
      </Button>
    </div>
  );
}
