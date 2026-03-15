import { useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { useNavigate } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { parseApiError } from "@/lib/utils";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Copy, Check } from "lucide-react";
import logoSrc from "@/assets/logo.png";
import { useTranslation } from "react-i18next";

export function Setup() {
  const { t } = useTranslation("auth", { keyPrefix: "setup" });
  const appName = useAppName();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [keyCopied, setKeyCopied] = useState(false);

  const passwordsMatch = password === confirmPassword;
  const passwordValid = password.length >= 8;
  const usernameValid = username.length >= 2;
  const canSubmit =
    usernameValid && passwordValid && passwordsMatch && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setLoading(true);

    try {
      const result = await api.setup.create({
        username,
        password,
        email: email || undefined,
      });
      setApiKey(result.api_key);
    } catch (err) {
      setError(parseApiError(err, t("errors.setupFailed")));
    } finally {
      setLoading(false);
    }
  };

  if (apiKey) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-sage-bg flex items-center justify-center mb-4">
              <Check className="w-6 h-6 text-sage" />
            </div>
            <h1 className="text-xl font-semibold text-ink">{t("complete.title")}</h1>
            <p className="text-sm text-ink-tertiary mt-1">
              {t("complete.description")}
            </p>
          </div>

          <div className="bg-surface rounded-xl border border-line p-6 space-y-4">
            <div className="p-4 rounded-xl border border-sage bg-sage-bg space-y-3">
              <p className="text-sm font-semibold text-sage">
                {t("complete.apiKeyTitle")}
              </p>
              <p className="text-xs text-ink-secondary">
                {t("complete.apiKeyDescription")}
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2.5 rounded-lg bg-canvas-tertiary border border-line font-mono text-xs select-all text-ink break-all">
                  {apiKey}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(apiKey);
                    setKeyCopied(true);
                  }}
                  className="shrink-0 p-2 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all"
                >
                  {keyCopied ? (
                    <Check size={16} className="text-sage" />
                  ) : (
                    <Copy size={16} />
                  )}
                </button>
              </div>
            </div>

            <Button
              size="lg"
              onClick={() => {
                queryClient.clear();
                navigate({ to: "/" });
              }}
              className="w-full"
            >
              {t("complete.continue")}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <img src={logoSrc} alt={appName} height={48} className="h-12 w-auto mb-4 drop-shadow-lg" />
          <h1 className="text-xl font-semibold text-ink">
            {t("welcome.title", { appName })}
          </h1>
          <p className="text-sm text-ink-tertiary mt-1">
            {t("welcome.description")}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface rounded-xl border border-line p-6 space-y-4"
        >
          {error && (
            <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-rust-bg border border-rust">
              <div className="w-1.5 h-1.5 rounded-full bg-rust shrink-0" />
              <p className="text-sm text-rust">{error}</p>
            </div>
          )}

          <Input
            id="username"
            label={t("fields.username.label")}
            type="text"
            autoComplete="username"
            autoFocus
            required
            minLength={2}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <Input
            id="email"
            label={`${t("fields.email.label")} ${t("fields.email.optionalHint")}`}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t("fields.email.placeholder")}
          />

          <Input
            id="password"
            label={t("fields.password.label")}
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t("fields.password.placeholder")}
          />

          <Input
            id="confirmPassword"
            label={t("fields.confirmPassword.label")}
            type="password"
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder={t("fields.confirmPassword.placeholder")}
            error={confirmPassword && !passwordsMatch ? t("fields.confirmPassword.mismatch") : undefined}
          />

          <Button
            type="submit"
            size="lg"
            disabled={!canSubmit}
            className="w-full"
          >
            {loading ? t("actions.creatingAccount") : t("actions.createAdminAccount")}
          </Button>
        </form>
      </div>
    </div>
  );
}
