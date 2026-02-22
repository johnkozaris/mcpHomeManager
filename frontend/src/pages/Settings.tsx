import { Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useHealth } from "@/hooks/useServices";
import { api } from "@/lib/api";
import { useTheme } from "@/hooks/useTheme";
import { useCurrentUser } from "@/hooks/useAuth";
import { getMcpEndpoint } from "@/lib/utils";
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
} from "lucide-react";
import { useState, useEffect } from "react";
import { parseApiError } from "@/lib/utils";

export function Settings() {
  const { data: health } = useHealth();
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.health.config,
  });
  const { theme, toggle } = useTheme();
  const { data: currentUserData } = useCurrentUser();
  const mcpEndpoint = getMcpEndpoint();
  const [copied, setCopied] = useState(false);
  const currentUser =
    currentUserData?.username ?? localStorage.getItem("username");
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
  const generateKey = useMutation({
    mutationFn: () => api.auth.createApiKey(),
    onSuccess: (data) => {
      setNewApiKey(data.api_key);
      setKeyCopied(false);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
  const revokeKey = useMutation({
    mutationFn: () => api.auth.revokeApiKey(),
    onSuccess: () => {
      setNewApiKey(null);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
  const hasApiKey = currentUserData?.has_api_key ?? false;
  const isAdmin = currentUserData?.is_admin ?? false;
  const toggleSelfMcp = useMutation({
    mutationFn: () => api.admin.setSelfMcp(!config?.self_mcp_enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
  });

  // SMTP config state
  const { data: smtpConfig } = useQuery({
    queryKey: ["admin", "smtp"],
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
  const [smtpTestResult, setSmtpTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

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
      queryClient.invalidateQueries({ queryKey: ["admin", "smtp"] });
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
  });

  const testSmtp = useMutation({
    mutationFn: () => api.admin.testSmtp(),
    onSuccess: (data) => setSmtpTestResult(data),
    onError: (err) =>
      setSmtpTestResult({
        success: false,
        message: parseApiError(err, "Test failed"),
      }),
  });

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="page-header">Settings</h1>
        <p className="page-description">
          Appearance, endpoints, and system info
        </p>
      </div>

      {/* Two-column grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          {/* Theme */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-clay-bg">
                  <Palette size={16} className="text-clay" />
                </div>
                <CardTitle>Appearance</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                onClick={() => theme === "dark" && toggle()}
                className={`p-4 rounded-xl border-2 transition-all text-center ${theme === "light" ? "border-terra bg-terra-bg" : "border-line hover:border-line-strong"}`}
              >
                <Sun size={20} className="mx-auto mb-2 text-clay" />
                <p className="text-sm font-semibold text-ink">Light</p>
              </button>
              <button
                onClick={() => theme === "light" && toggle()}
                className={`p-4 rounded-xl border-2 transition-all text-center ${theme === "dark" ? "border-terra bg-terra-bg" : "border-line hover:border-line-strong"}`}
              >
                <Moon size={20} className="mx-auto mb-2 text-info" />
                <p className="text-sm font-semibold text-ink">Dark</p>
              </button>
            </div>
          </Card>

          {/* Security */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-sage-bg">
                  <Shield size={16} className="text-sage" />
                </div>
                <CardTitle>Security</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-0">
              <div className="py-3 border-b border-line">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Wrench size={15} className="text-ink-tertiary" />
                    <span className="text-sm font-medium text-ink">
                      Self-MCP Tools
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
                      {config?.self_mcp_enabled ? "Enabled" : "Disabled"}
                    </Badge>
                  )}
                </div>
                <p className="text-2xs text-ink-tertiary mt-2 leading-relaxed">
                  When enabled, AI agents can manage this gateway through MCP
                  itself — listing services, toggling tools, adding connections,
                  and viewing logs without using the web UI.
                  {config?.self_mcp_enabled && (
                    <>
                      {" "}
                      Access is granted per-user in{" "}
                      <Link to="/users" className="text-terra hover:underline">
                        User Management
                      </Link>
                      .
                    </>
                  )}
                </p>
                <p className="text-2xs text-ink-faint mt-1">
                  Defaults from{" "}
                  <code className="font-mono">SELF_MCP_ENABLED</code> env var on
                  restart.
                </p>
              </div>
              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-2.5">
                  <User size={15} className="text-ink-tertiary" />
                  <span className="text-sm text-ink-secondary">
                    Signed in as{" "}
                    <span className="font-semibold text-ink">
                      {currentUser ?? "admin"}
                    </span>
                  </span>
                </div>
              </div>
            </div>

            {/* API Key Management */}
            <div className="mt-3 pt-3 border-t border-line">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Key size={15} className="text-ink-tertiary" />
                  <span className="text-sm font-medium text-ink">
                    MCP API Key
                  </span>
                </div>
                <Badge variant={hasApiKey ? "positive" : "default"}>
                  {hasApiKey ? "Active" : "Not set"}
                </Badge>
              </div>
              <p className="text-2xs text-ink-tertiary mb-3">
                AI agents (Claude, Cursor, ChatGPT) use this key to connect to
                your MCP endpoint.
              </p>

              {newApiKey && (
                <div className="p-3 rounded-xl border border-sage bg-sage-bg space-y-2 mb-3">
                  <p className="text-xs font-semibold text-sage">
                    Save this key — it won't be shown again
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

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => generateKey.mutate()}
                  disabled={generateKey.isPending}
                >
                  <Key size={13} />
                  {hasApiKey ? "Regenerate Key" : "Generate Key"}
                </Button>
                {hasApiKey && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowRevokeConfirm(true)}
                    disabled={revokeKey.isPending}
                  >
                    <Trash2 size={13} />
                    Revoke
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* About */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-info-bg">
                  <Info size={16} className="text-info" />
                </div>
                <CardTitle>About</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-2 text-sm text-ink-secondary">
              <div className="flex justify-between">
                <span>Version</span>
                <span className="text-ink font-mono font-bold">0.1.0</span>
              </div>
              <div className="flex justify-between">
                <span>Server</span>
                <span className="text-ink-tertiary">
                  {config?.mcp_server_name ?? "MCP Manager"}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* MCP Endpoint */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-terra-bg">
                  <Terminal size={16} className="text-terra" />
                </div>
                <CardTitle>MCP Endpoint</CardTitle>
              </div>
            </CardHeader>
            <p className="text-sm text-ink-secondary mt-2 mb-3">
              Your AI agents connect to this URL
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
              <Bot size={14} /> Agent setup guide <ArrowRight size={12} />
            </Link>
          </Card>

          {/* System Health */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-sage-bg">
                  <HeartPulse size={16} className="text-sage" />
                </div>
                <CardTitle>System Health</CardTitle>
              </div>
            </CardHeader>
            <div className="mt-3 space-y-0">
              {[
                {
                  icon: Database,
                  label: "Database",
                  value: health?.database ?? "checking",
                  ok: health?.database === "connected",
                },
                {
                  icon: Server,
                  label: "MCP Server",
                  value: health?.mcp_server ?? "checking",
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
                  <span className="text-sm text-ink-secondary">Services</span>
                </div>
                <span className="text-sm text-ink font-semibold">
                  {health?.services_healthy ?? 0} /{" "}
                  {health?.services_total ?? 0} connected
                </span>
              </div>
            </div>
          </Card>
          {/* SMTP / Email Configuration (admin only) */}
          {isAdmin && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-terra-bg">
                    <Mail size={16} className="text-terra" />
                  </div>
                  <CardTitle>Email (SMTP)</CardTitle>
                </div>
              </CardHeader>
              <p className="text-2xs text-ink-tertiary mt-2 mb-3">
                Configure SMTP for password reset emails. Leave blank to
                disable.
              </p>
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-2">
                    <label
                      htmlFor="smtp-host"
                      className="block text-2xs font-medium text-ink-secondary mb-1"
                    >
                      Host
                    </label>
                    <input
                      id="smtp-host"
                      type="text"
                      value={smtpHost}
                      onChange={(e) => setSmtpHost(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                      placeholder="smtp.gmail.com"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="smtp-port"
                      className="block text-2xs font-medium text-ink-secondary mb-1"
                    >
                      Port
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
                    className="block text-2xs font-medium text-ink-secondary mb-1"
                  >
                    Username
                  </label>
                  <input
                    id="smtp-username"
                    type="text"
                    value={smtpUsername}
                    onChange={(e) => setSmtpUsername(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder="user@example.com"
                  />
                </div>
                <div>
                  <label className="block text-2xs font-medium text-ink-secondary mb-1">
                    Password{" "}
                    {smtpConfig?.has_password && (
                      <span className="text-ink-faint">
                        (set — leave blank to keep)
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    value={smtpPassword}
                    onChange={(e) => setSmtpPassword(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder={
                      smtpConfig?.has_password ? "••••••••" : "App password"
                    }
                  />
                </div>
                <div>
                  <label
                    htmlFor="smtp-from"
                    className="block text-2xs font-medium text-ink-secondary mb-1"
                  >
                    From Email
                  </label>
                  <input
                    id="smtp-from"
                    type="email"
                    value={smtpFrom}
                    onChange={(e) => setSmtpFrom(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg border border-line bg-canvas text-ink text-sm"
                    placeholder="noreply@example.com"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink-secondary">
                    Use TLS (STARTTLS)
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
                  <span className="text-sm text-ink-secondary">Enabled</span>
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
                      "Failed to save SMTP config",
                    )}
                  </div>
                )}

                {smtpTestResult && (
                  <div
                    className={`p-2.5 rounded-lg text-xs ${smtpTestResult.success ? "bg-sage-bg text-sage border border-sage" : "bg-rust-bg text-rust border border-rust"}`}
                  >
                    {smtpTestResult.message}
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
                        <Check size={13} /> Saved
                      </>
                    ) : saveSmtp.isPending ? (
                      "Saving…"
                    ) : (
                      "Save"
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
                    {testSmtp.isPending ? "Sending…" : "Send Test Email"}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={showRevokeConfirm}
        title="Revoke API Key"
        description="This will immediately disconnect any AI agents using this key. You can generate a new key afterwards."
        confirmText="Revoke Key"
        onConfirm={() => {
          revokeKey.mutate();
          setShowRevokeConfirm(false);
        }}
        onCancel={() => setShowRevokeConfirm(false)}
      />
    </div>
  );
}
