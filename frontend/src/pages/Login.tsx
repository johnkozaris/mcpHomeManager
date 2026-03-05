import { useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { queryClient } from "@/lib/queryClient";
import { parseApiError } from "@/lib/utils";
import { Home } from "lucide-react";
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
          <div className="w-12 h-12 rounded-xl bg-terra-bg flex items-center justify-center mb-4">
            <Home className="w-6 h-6 text-terra" />
          </div>
          <h1 className="text-xl font-semibold text-ink">{appName}</h1>
          <p className="text-sm text-ink-muted mt-1">
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

          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              {t("fields.username.label")}
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                         placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                         transition-colors"
              placeholder={t("fields.username.placeholder")}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              {t("fields.password.label")}
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                         placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                         transition-colors"
              placeholder={t("fields.password.placeholder")}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !username || !password}
              className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                       hover:bg-terra-hover active:scale-[0.98] transition-all
                       disabled:opacity-50 disabled:pointer-events-none"
          >
            {loading ? t("actions.signingIn") : t("actions.signIn")}
          </button>

          <div className="h-6 text-center">
            {config?.smtp_enabled && (
              <Link
                to="/forgot-password"
                className="text-sm text-ink-muted hover:text-terra transition-colors"
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
