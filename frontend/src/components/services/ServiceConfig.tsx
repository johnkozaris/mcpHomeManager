import { useState } from "react";
import type {
  BuiltinServiceType,
  CreateServiceRequest,
  ServiceType,
} from "@/lib/types";
import { BUILTIN_SERVICE_TYPES } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SERVICE_META, getServiceMeta } from "@/lib/service-meta";
import { getTokenGuides } from "@/lib/token-guides";
import { useAppName } from "@/hooks/useAppName";
import { HelpCircle } from "lucide-react";

interface Prefill {
  name: string;
  displayName: string;
  type: ServiceType;
  baseUrl: string;
}

interface Props {
  onSubmit: (data: CreateServiceRequest) => void;
  isLoading?: boolean;
  initialType?: ServiceType;
  prefill?: Prefill;
}

export function ServiceConfig({
  onSubmit,
  isLoading,
  initialType,
  prefill,
}: Props) {
  const [name, setName] = useState(prefill?.name ?? initialType ?? "");
  const [displayName, setDisplayName] = useState(
    prefill?.displayName ??
      (initialType ? getServiceMeta(initialType).label : ""),
  );
  const [serviceType, setServiceType] = useState<ServiceType>(
    prefill?.type ?? initialType ?? "forgejo",
  );
  const [baseUrl, setBaseUrl] = useState(prefill?.baseUrl ?? "");
  const [apiToken, setApiToken] = useState("");
  const [guideOpen, setGuideOpen] = useState(false);
  const appName = useAppName();
  const tokenGuides = getTokenGuides(appName);

  const serviceTypes = Object.entries(SERVICE_META).map(([value, meta]) => ({
    value: value as ServiceType,
    label: meta.label,
  }));

  const guide = (BUILTIN_SERVICE_TYPES as readonly string[]).includes(
    serviceType,
  )
    ? tokenGuides[serviceType as BuiltinServiceType]
    : undefined;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          name,
          display_name: displayName,
          service_type: serviceType,
          base_url: baseUrl,
          api_token: apiToken.trim(),
        });
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Identifier"
          placeholder="forgejo"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Input
          label="Display Name"
          placeholder="Forgejo"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <label
          htmlFor="service-type"
          className="block text-sm font-medium text-ink-secondary"
        >
          Service Type
        </label>
        <select
          id="service-type"
          value={serviceType}
          onChange={(e) => setServiceType(e.target.value as ServiceType)}
          className="input-field"
        >
          {serviceTypes.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      <Input
        label="Base URL"
        placeholder="https://service.example.com"
        value={baseUrl}
        onChange={(e) => setBaseUrl(e.target.value)}
        onBlur={() => {
          const trimmed = baseUrl.trim();
          if (trimmed && !/^https?:\/\//i.test(trimmed)) {
            setBaseUrl(`https://${trimmed}`);
          }
        }}
        required
      />
      <div>
        <Input
          label="API Token"
          type="password"
          placeholder="Paste your API token"
          value={apiToken}
          onChange={(e) => setApiToken(e.target.value)}
          required
        />
        {guide && (
          <button
            type="button"
            onClick={() => setGuideOpen(!guideOpen)}
            className="flex items-center gap-1 mt-1.5 text-xs text-terra hover:text-terra-light transition-colors"
          >
            <HelpCircle size={12} />
            {guideOpen ? "Hide" : "How to get"} a{" "}
            {getServiceMeta(serviceType).label} token
          </button>
        )}
        {guideOpen && guide && (
          <div className="mt-2 p-3 rounded-lg bg-canvas-secondary border border-line text-xs space-y-1.5">
            <ol className="list-decimal list-inside space-y-1 text-ink-secondary">
              {guide.steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
            {guide.note && (
              <p className="text-ink-tertiary italic">{guide.note}</p>
            )}
          </div>
        )}
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Connecting\u2026" : "Connect Service"}
        </Button>
      </div>
    </form>
  );
}
