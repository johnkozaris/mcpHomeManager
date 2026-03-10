import { Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useHealth } from "@/hooks/useServices";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { useTheme } from "@/hooks/useTheme";
import { useCurrentUser } from "@/hooks/useAuth";
import { getMcpEndpoint, parseApiError, resolveBackendMessage } from "@/lib/utils";
import type { SmtpTestResult } from "@/lib/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import {
  Terminal,
  Database,
  Server,
  HeartPulse,
  Copy,
  Sun,
  Moon,
  Bot,
  Info,
  ArrowRight,
  Wrench,
  Mail,
  Palette,
  Shield,
  Check,
  User,
  Key,
  Trash2,
  Eye,
  Globe,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  SUPPORTED_LOCALES,
  LOCALE_DISPLAY_NAMES,
  type SupportedLocale,
} from "@/i18n/config";

export function Settings() {
  const { t, i18n } = useTranslation("settings", { keyPrefix: "page" });
  const currentLocale = (i18n.language ?? "en") as SupportedLocale;
  const { data: health } = useHealth();
  const { data: config } = useQuery({
    queryKey: queryKeys.config(),
    queryFn: api.health.config,
  });
  const { theme, toggle } = useTheme();
  const { data: currentUserData } = useCurrentUser();
  const mcpEndpoint = getMcpEndpoint();
  const [copied, setCopied] = useState(false);
  const currentUser = currentUserData?.username ?? null;
  useEffect(() => {
    if (!copied) return;
    const id = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(id);
  }, [copied]);
  const copy = () => {
    navigator.clipboard.writeText(mcpEndpoint);
    setCopied(true);
  };

  const queryClient = useQueryClient();
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false);
  const [keyCopied, setKeyCopied] = useState(false);
  const [revealError, setRevealError] = useState<string | null>(null);
  const generateKey = useMutation({
    mutationFn: () => api.auth.createApiKey(),
    onSuccess: (data) => {
      setNewApiKey(data.api_key);
      setKeyCopied(false);
      queryClient.invalidateQueries({ queryKey: queryKeys.authMe() });
    },
  });
  const revokeKey = useMutation({
    mutationFn: () => api.auth.revokeApiKey(),
    onSuccess: () => {
      setNewApiKey(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.authMe() });
    },
  });
  const hasApiKey = currentUserData?.has_api_key ?? false;
  const canReveal = currentUserData?.can_reveal_api_key ?? false;
  const isAdmin = currentUserData?.is_admin ?? false;
  const toggleSelfMcp = useMutation({
    mutationFn: () => api.admin.setSelfMcp(!config?.self_mcp_enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config() });
    },
  });

  const { data: smtpConfig } = useQuery({
    queryKey: queryKeys.adminSmtp(),
    queryFn: api.admin.getSmtp,
    enabled: isAdmin,
  });
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("587");
  const [smtpUsername, setSmtpUsername] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [smtpFrom, setSmtpFrom] = useState("");
  const [smtpTls, setSmtpTls] = useState(true);
  const [smtpEnabled, setSmtpEnabled] = useState(true);
  const [smtpSynced, setSmtpSynced] = useState<typeof smtpConfig>(undefined);
  const [smtpSaved, setSmtpSaved] = useState(false);
  const [smtpTestResult, setSmtpTestResult] = useState<SmtpTestResult | null>(
    null,
  );
  const smtpTestMessage = smtpTestResult
    ? resolveBackendMessage(smtpTestResult, {
        fallback: smtpTestResult.message,
        includeRawDetail: true,
      })
    : null;

  // Sync server data into form state (adjusting state during render)
  if (smtpConfig && smtpConfig !== smtpSynced) {
    setSmtpSynced(smtpConfig);
    setSmtpHost(smtpConfig.host);
    setSmtpPort(String(smtpConfig.port));
    setSmtpUsername(smtpConfig.username ?? "");
    setSmtpFrom(smtpConfig.from_email);
    setSmtpTls(smtpConfig.use_tls);
    setSmtpEnabled(smtpConfig.is_enabled);
  }

  const saveSmtp = useMutation({
    mutationFn: () =>
      api.admin.updateSmtp({
        host: smtpHost,
        port: parseInt(smtpPort, 10) || 587,
        username: smtpUsername || null,
        password: smtpPassword || null,
        from_email: smtpFrom,
        use_tls: smtpTls,
        is_enabled: smtpEnabled,
      }),
    onSuccess: () => {
      setSmtpPassword("");
      setSmtpSaved(true);
      setSmtpSynced(undefined); // re-sync form from server on next refetch
      setTimeout(() => setSmtpSaved(false), 2000);
      queryClient.invalidateQueries({ queryKey: queryKeys.adminSmtp() });
      queryClient.invalidateQueries({ queryKey: queryKeys.config() });
    },
  });

  const testSmtp = useMutation({
    mutationFn: () => api.admin.testSmtp(),
    onSuccess: (data) => setSmtpTestResult(data),
    onError: (err) =>
      setSmtpTestResult({
        success: false,
        message: parseApiError(err, t("smtp.testFailed")),
      }),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-header">{t("title")}</h1>
        <p className="page-description">{t("description")}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-clay-bg">
                  <Palette size={16} className="text-clay" />
                </div>
                <CardTitle>{t("appearance.title")}</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                onClick={() => theme === "dark" && toggle()}
                className={`p-4 rounded-xl border-2 transition-all text-center ${theme === "light" ? "border-terra bg-terra-bg" : "border-line hover:border-line-strong"}`}
              >
                <Sun size={20} className="mx-auto mb-2 text-clay" />
                <p className="text-sm font-semibold text-ink">
                  {t("appearance.light")}
                </p>
              </button>
              <button
                onClick={() => theme === "light" && toggle()}
                className={`p-4 rounded-xl border-2 transition-all text-center ${theme === "dark" ? "border-terra bg-terra-bg" : "border-line hover:border-line-strong"}`}
              >
                <Moon size={20} className="mx-auto mb-2 text-info" />
                <p className="text-sm font-semibold text-ink">
                  {t("appearance.dark")}
                </p>
              </button>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-terra-bg">
                  <Globe size={16} className="text-terra" />
                </div>
                <CardTitle>{t("language.title")}</CardTitle>
              </div>
            </CardHeader>
            <p className="text-xs text-ink-tertiary mt-1 mb-3">
              {t("language.description")}
            </p>
            <div className="grid grid-cols-2 gap-2">
              {SUPPORTED_LOCALES.map((locale) => (
                <button
                  key={locale}
                  onClick={() => i18n.changeLanguage(locale)}
                  className={`px-3 py-2.5 rounded-xl border-2 transition-all text-left ${
                    currentLocale === locale
                      ? "border-terra bg-terra-bg"
                      : "border-line hover:border-line-strong"
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${currentLocale === locale ? "text-terra" : "text-ink"}`}
                  >
                    {LOCALE_DISPLAY_NAMES[locale]}
                  </p>
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-sage-bg">
                  <Shield size={16} className="text-sage" />
                </div>
                <CardTitle>{t("security.title")}</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-0">
              <div className="py-3 border-b border-line">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Wrench size={15} className="text-ink-tertiary" />
                    <span className="text-sm font-medium text-ink">
                      {t("security.selfMcp.title")}
                    </span>
                  </div>
                  {isAdmin ? (
                    <button
                      onClick={() => toggleSelfMcp.mutate()}
                      disabled={toggleSelfMcp.isPending}
                      className={`w-10 h-5 rounded-full transition-colors ${config?.self_mcp_enabled ? "bg-terra" : "bg-line-strong"}`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${config?.self_mcp_enabled ? "translate-x-5" : "translate-x-0.5"}`}
                      />
                    </button>
                  ) : (
                    <Badge
                      variant={
                        config?.self_mcp_enabled ? "positive" : "default"
                      }
                    >
                      {config?.self_mcp_enabled
                        ? t("security.enabled")
                        : t("security.disabled")}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-ink-tertiary mt-2 leading-relaxed">
                  {t("security.selfMcp.description")}
                  {config?.self_mcp_enabled && (
                    <>
                      {" "}
                      {t("security.selfMcp.accessPrefix")}{" "}
                      <Link to="/users" className="text-terra hover:underline">
                        {t("security.selfMcp.userManagementLink")}
                      </Link>
                      {t("security.selfMcp.accessSuffix")}
                    </>
                  )}
                </p>
                {config?.self_mcp_enabled && (
                  <p className="text-xs text-ink-faint mt-1 leading-relaxed">
                    {t("security.selfMcp.restartHint")}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-2.5">
                  <User size={15} className="text-ink-tertiary" />
                  <span className="text-sm text-ink-secondary">
                    {t("security.signedInAs")}{" "}
                    <span className="font-semibold text-ink">
                      {currentUser ?? t("security.currentUserFallback")}
                    </span>
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-line">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Key size={15} className="text-ink-tertiary" />
                  <span className="text-sm font-medium text-ink">
                    {t("apiKey.title")}
                  </span>
                </div>
                <Badge variant={hasApiKey ? "positive" : "default"}>
                  {hasApiKey ? t("apiKey.status.active") : t("apiKey.status.notSet")}
                </Badge>
              </div>
              <p className="text-xs text-ink-tertiary mb-3">
                {t("apiKey.description")}
              </p>

              {newApiKey && (
                <div className="p-3 rounded-xl border border-sage bg-sage-bg space-y-2 mb-3">
                  <p className="text-xs font-semibold text-sage">
                    {t("apiKey.revealedTitle")}
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-2 rounded-lg bg-canvas-tertiary border border-line font-mono text-xs select-all text-ink break-all">
                      {newApiKey}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(newApiKey);
                        setKeyCopied(true);
                      }}
                      className="shrink-0 p-1.5 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all"
                    >
                      {keyCopied ? (
                        <Check size={14} className="text-sage" />
                      ) : (
                        <Copy size={14} />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {revealError && (
                <div className="p-2.5 rounded-lg text-xs bg-rust-bg text-rust border border-rust mb-3">
                  {revealError}
                </div>
              )}

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    setRevealError(null);
                    generateKey.mutate();
                  }}
                  disabled={generateKey.isPending}
                >
                  <Key size={13} />
                  {hasApiKey
                    ? t("apiKey.actions.regenerate")
                    : t("apiKey.actions.generate")}
                </Button>
                {hasApiKey && !newApiKey && canReveal && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      try {
                        const data = await api.auth.getApiKey();
                        setNewApiKey(data.api_key);
                        setKeyCopied(false);
                      } catch (err) {
                        setRevealError(
                          parseApiError(
                            err,
                            t("apiKey.errors.revealFailed"),
                          ),
                        );
                      }
                    }}
                  >
                    <Eye size={13} />
                    {t("apiKey.actions.reveal")}
                  </Button>
                )}
                {hasApiKey && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowRevokeConfirm(true)}
                    disabled={revokeKey.isPending}
                  >
                    <Trash2 size={13} />
                    {t("apiKey.actions.revoke")}
                  </Button>
                )}
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-info-bg">
                  <Info size={16} className="text-info" />
                </div>
                <CardTitle>{t("about.title")}</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-2 text-sm text-ink-secondary">
              <div className="flex justify-between">
                <span>{t("about.versionLabel")}</span>
                <span className="text-ink font-mono font-bold">{__APP_VERSION__}</span>
              </div>
              <div className="flex justify-between">
                <span>{t("about.serverLabel")}</span>
                <span className="text-ink-tertiary">
                  {config?.mcp_server_name ?? t("about.serverFallback")}
                </span>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-terra-bg">
                  <Terminal size={16} className="text-terra" />
                </div>
                <CardTitle>{t("endpoint.title")}</CardTitle>
              </div>
            </CardHeader>
            <p className="text-sm text-ink-secondary mt-2 mb-3">
              {t("endpoint.description")}
            </p>
            <div className="flex items-center gap-2 p-3 rounded-xl bg-canvas">
              <code className="text-sm font-mono text-ink flex-1 truncate">
                {mcpEndpoint}
              </code>
              <button
                onClick={copy}
                className="shrink-0 px-3 py-1.5 rounded-xl text-xs font-bold bg-(--coral) text-white hover:opacity-90 transition-opacity"
              >
                {copied ? <Check size={13} /> : <Copy size={13} />}
              </button>
            </div>
            <Link
              to="/agents"
              className="flex items-center gap-1.5 text-sm font-medium text-terra hover:text-terra-light transition-colors mt-4"
            >
              <Bot size={14} /> {t("endpoint.agentGuide")} <ArrowRight size={12} />
            </Link>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-sage-bg">
                  <HeartPulse size={16} className="text-sage" />
                </div>
                <CardTitle>{t("systemHealth.title")}</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-0">
              {[
                {
                  icon: Database,
                  label: t("systemHealth.rows.database"),
                  value: health?.database ?? t("systemHealth.checking"),
                  ok: health?.database === "connected",
                },
                {
                  icon: Server,
                  label: t("systemHealth.rows.mcpServer"),
                  value: health?.mcp_server ?? t("systemHealth.checking"),
                  ok: health?.mcp_server === "running",
                },
              ].map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between py-3 border-b border-line last:border-0"
                >
                  <div className="flex items-center gap-2.5">
                    <row.icon size={15} className="text-ink-tertiary" />
                    <span className="text-sm text-ink-secondary">
                      {row.label}
                    </span>
                  </div>
                  <Badge variant={row.ok ? "positive" : "critical"}>
                    {row.value}
                  </Badge>
                </div>
              ))}
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-2.5">
                  <HeartPulse size={15} className="text-ink-tertiary" />
                  <span className="text-sm text-ink-secondary">
                    {t("systemHealth.rows.services")}
                  </span>
                </div>
                <span className="text-sm text-ink font-semibold">
                  {t("systemHealth.servicesConnected", {
                    healthy: health?.services_healthy ?? 0,
                    total: health?.services_total ?? 0,
                  })}
                </span>
              </div>
            </div>
          </Card>
          {isAdmin && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-terra-bg">
                  <Mail size={16} className="text-terra" />
                </div>
                  <CardTitle>{t("smtp.title")}</CardTitle>
                </div>
              </CardHeader>
              <p className="text-xs text-ink-tertiary mt-2 mb-3">
                {t("smtp.description")}
              </p>
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-2">
                    <label
                      htmlFor="smtp-host"
                      className="block text-xs font-medium text-ink-secondary mb-1"
                    >
                      {t("smtp.fields.host")}
                    </label>
                    <input
                      id="smtp-host"
                      type="text"
                      value={smtpHost}
                      onChange={(e) => setSmtpHost(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                      placeholder={t("smtp.placeholders.host")}
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="smtp-port"
                      className="block text-xs font-medium text-ink-secondary mb-1"
                    >
                      {t("smtp.fields.port")}
                    </label>
                    <input
                      id="smtp-port"
                      type="number"
                      value={smtpPort}
                      onChange={(e) => setSmtpPort(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="smtp-username"
                    className="block text-xs font-medium text-ink-secondary mb-1"
                  >
                    {t("smtp.fields.username")}
                  </label>
                  <input
                    id="smtp-username"
                    type="text"
                    value={smtpUsername}
                    onChange={(e) => setSmtpUsername(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder={t("smtp.placeholders.username")}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-secondary mb-1">
                    {t("smtp.fields.password")}{" "}
                    {smtpConfig?.has_password && (
                      <span className="text-ink-faint">
                        {t("smtp.fields.passwordHint")}
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    value={smtpPassword}
                    onChange={(e) => setSmtpPassword(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder={
                      smtpConfig?.has_password
                        ? t("smtp.placeholders.passwordMasked")
                        : t("smtp.placeholders.password")
                    }
                  />
                </div>
                <div>
                  <label
                    htmlFor="smtp-from"
                    className="block text-xs font-medium text-ink-secondary mb-1"
                  >
                    {t("smtp.fields.fromEmail")}
                  </label>
                  <input
                    id="smtp-from"
                    type="email"
                    value={smtpFrom}
                    onChange={(e) => setSmtpFrom(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder={t("smtp.placeholders.fromEmail")}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink-secondary">
                    {t("smtp.toggles.useTls")}
                  </span>
                  <button
                    onClick={() => setSmtpTls(!smtpTls)}
                    className={`w-10 h-5 rounded-full transition-colors ${smtpTls ? "bg-terra" : "bg-line-strong"}`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${smtpTls ? "translate-x-5" : "translate-x-0.5"}`}
                    />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink-secondary">
                    {t("smtp.toggles.enabled")}
                  </span>
                  <button
                    onClick={() => setSmtpEnabled(!smtpEnabled)}
                    className={`w-10 h-5 rounded-full transition-colors ${smtpEnabled ? "bg-terra" : "bg-line-strong"}`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${smtpEnabled ? "translate-x-5" : "translate-x-0.5"}`}
                    />
                  </button>
                </div>

                {saveSmtp.isError && (
                  <div className="p-2.5 rounded-lg text-xs bg-rust-bg text-rust border border-rust">
                    {parseApiError(
                      saveSmtp.error,
                      t("smtp.errors.saveFailed"),
                    )}
                  </div>
                )}

                {smtpTestResult && (
                  <div
                    className={`p-2.5 rounded-lg text-xs ${smtpTestResult.success ? "bg-sage-bg text-sage border border-sage" : "bg-rust-bg text-rust border border-rust"}`}
                  >
                    {smtpTestMessage ?? smtpTestResult.message}
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  <Button
                    size="sm"
                    onClick={() => saveSmtp.mutate()}
                    disabled={saveSmtp.isPending || !smtpHost}
                  >
                    {smtpSaved ? (
                      <>
                        <Check size={13} /> {t("smtp.actions.saved")}
                      </>
                    ) : saveSmtp.isPending ? (
                      t("smtp.actions.saving")
                    ) : (
                      t("smtp.actions.save")
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSmtpTestResult(null);
                      testSmtp.mutate();
                    }}
                    disabled={testSmtp.isPending || !smtpConfig?.is_enabled}
                  >
                    {testSmtp.isPending
                      ? t("smtp.actions.sending")
                      : t("smtp.actions.sendTestEmail")}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={showRevokeConfirm}
        title={t("dialogs.revokeKey.title")}
        description={t("dialogs.revokeKey.description")}
        confirmText={t("dialogs.revokeKey.confirm")}
        onConfirm={() => {
          revokeKey.mutate();
          setShowRevokeConfirm(false);
        }}
        onCancel={() => setShowRevokeConfirm(false)}
      />
    </div>
  );
}
