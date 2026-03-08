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
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation("components", {
    keyPrefix: "services.serviceConfig",
  });
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

  const serviceTypes = BUILTIN_SERVICE_TYPES.map((value) => ({
    value,
    label: SERVICE_META[value].label,
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
          label={t("identifierLabel")}
          placeholder={t("identifierPlaceholder")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Input
          label={t("displayNameLabel")}
          placeholder={t("displayNamePlaceholder")}
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
          {t("serviceTypeLabel")}
        </label>
        <select
          id="service-type"
          value={serviceType}
          onChange={(e) => setServiceType(e.target.value as ServiceType)}
          className="input-field"
        >
          {serviceTypes.map((serviceTypeOption) => (
            <option
              key={serviceTypeOption.value}
              value={serviceTypeOption.value}
            >
              {serviceTypeOption.label}
            </option>
          ))}
        </select>
      </div>
      <Input
        label={t("baseUrlLabel")}
        placeholder={t("baseUrlPlaceholder")}
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
          label={t("apiTokenLabel")}
          type="password"
          placeholder={t("apiTokenPlaceholder")}
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
            {guideOpen
              ? t("tokenGuideHide", { label: getServiceMeta(serviceType).label })
              : t("tokenGuideShow", { label: getServiceMeta(serviceType).label })}
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
          {isLoading ? t("connecting") : t("connectService")}
        </Button>
      </div>
    </form>
  );
}
