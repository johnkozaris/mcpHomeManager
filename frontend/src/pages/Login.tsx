import { useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { queryClient } from "@/lib/queryClient";
import { parseApiError } from "@/lib/utils";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import logoSrc from "@/assets/logo.png";
import { useTranslation } from "react-i18next";

export function Login() {
  const { t } = useTranslation("auth", { keyPrefix: "login" });
  const appName = useAppName();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: config } = useQuery({
    queryKey: queryKeys.config(),
    queryFn: api.health.config,
    staleTime: 60_000,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.auth.login(username, password);
      queryClient.clear();
      navigate({ to: "/" });
    } catch (err) {
      setError(parseApiError(err, t("errors.loginFailed")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <img src={logoSrc} alt={appName} height={48} className="h-12 w-auto mb-4 drop-shadow-sm" />
          <h1 className="text-xl font-semibold text-ink">{appName}</h1>
          <p className="text-sm text-ink-tertiary mt-1">
            {t("subtitle")}
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
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder={t("fields.username.placeholder")}
          />

          <Input
            id="password"
            label={t("fields.password.label")}
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t("fields.password.placeholder")}
          />

          <Button
            type="submit"
            size="lg"
            disabled={loading || !username || !password}
            className="w-full"
          >
            {loading ? t("actions.signingIn") : t("actions.signIn")}
          </Button>

          <div className="h-6 text-center">
            {config?.smtp_enabled && (
              <Link
                to="/forgot-password"
                className="text-sm text-ink-tertiary hover:text-terra transition-colors"
              >
                {t("actions.forgotPassword")}
              </Link>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
