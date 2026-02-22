import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import type { AuditEntry } from "@/lib/types";

interface Props {
  entry: AuditEntry;
  serviceId?: string;
}

export function LogEntryDetail({ entry, serviceId }: Props) {
  return (
    <div className="px-5 py-4 bg-canvas-secondary border-t border-line space-y-3">
      {entry.error_message && (
        <div className="p-3 rounded-lg bg-rust-bg border border-rust">
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-1">
            Error
          </p>
          <p className="text-xs text-rust font-mono whitespace-pre-wrap">
            {entry.error_message}
          </p>
        </div>
      )}

      {entry.input_summary && (
        <div>
          <p className="text-2xs text-ink-tertiary uppercase tracking-wider mb-1">
            Input
          </p>
          <p className="text-xs text-ink-secondary font-mono whitespace-pre-wrap">
            {entry.input_summary}
          </p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-ink-tertiary">
          <span>
            Duration:{" "}
            <span className="text-ink-secondary font-mono">
              {entry.duration_ms}ms
            </span>
          </span>
          {entry.client_name && (
            <span>
              Client:{" "}
              <span className="text-ink-secondary">{entry.client_name}</span>
            </span>
          )}
          {entry.created_at && (
            <span>
              Time:{" "}
              <span className="text-ink-secondary">
                {new Date(entry.created_at).toLocaleString()}
              </span>
            </span>
          )}
        </div>
        {serviceId && (
          <Link
            to="/services/$id"
            params={{ id: serviceId }}
            className="flex items-center gap-1 text-xs text-terra hover:text-terra-light transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            View Service
            <ArrowRight size={12} />
          </Link>
        )}
      </div>
    </div>
  );
}
