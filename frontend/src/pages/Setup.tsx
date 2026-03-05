import { useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { useNavigate } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { parseApiError } from "@/lib/utils";
import { Home, Copy, Check } from "lucide-react";
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
            <p className="text-sm text-ink-muted mt-1">
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

            <button
              onClick={() => {
                queryClient.clear();
                navigate({ to: "/" });
              }}
              className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                         hover:bg-terra-hover active:scale-[0.98] transition-all"
            >
              {t("complete.continue")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-terra-bg flex items-center justify-center mb-4">
            <Home className="w-6 h-6 text-terra" />
          </div>
          <h1 className="text-xl font-semibold text-ink">
            {t("welcome.title", { appName })}
          </h1>
          <p className="text-sm text-ink-muted mt-1">
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
              minLength={2}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                         placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                         transition-colors"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              {t("fields.email.label")}{" "}
              <span className="text-ink-faint font-normal">
                {t("fields.email.optionalHint")}
              </span>
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                         placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                         transition-colors"
              placeholder={t("fields.email.placeholder")}
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
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                         placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                         transition-colors"
              placeholder={t("fields.password.placeholder")}
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              {t("fields.confirmPassword.label")}
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
               className={`w-full px-3 py-2 rounded-lg border bg-canvas text-ink text-sm
                          placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                          transition-colors ${confirmPassword && !passwordsMatch ? "border-rust" : "border-line"}`}
               placeholder={t("fields.confirmPassword.placeholder")}
             />
             {confirmPassword && !passwordsMatch && (
               <p className="text-xs text-rust mt-1">
                 {t("fields.confirmPassword.mismatch")}
               </p>
             )}
           </div>

          <button
            type="submit"
            disabled={!canSubmit}
              className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                       hover:bg-terra-hover active:scale-[0.98] transition-all
                       disabled:opacity-50 disabled:pointer-events-none"
          >
            {loading ? t("actions.creatingAccount") : t("actions.createAdminAccount")}
          </button>
        </form>
      </div>
    </div>
  );
}
