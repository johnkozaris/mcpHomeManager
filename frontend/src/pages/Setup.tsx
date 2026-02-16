import { useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { useNavigate } from "@tanstack/react-router";
import { api, setSessionToken } from "@/lib/api";
import { parseApiError } from "@/lib/utils";
import { Home, Copy, Check } from "lucide-react";

export function Setup() {
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
      setSessionToken(result.token);
      localStorage.setItem("username", result.username);
      setApiKey(result.api_key);
    } catch (err) {
      setError(parseApiError(err, "Setup failed"));
    } finally {
      setLoading(false);
    }
  };

  // After setup, show the API key card
  if (apiKey) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-sage-bg flex items-center justify-center mb-4">
              <Check className="w-6 h-6 text-sage" />
            </div>
            <h1 className="text-xl font-semibold text-ink">Setup Complete</h1>
            <p className="text-sm text-ink-muted mt-1">
              Your admin account has been created
            </p>
          </div>

          <div className="bg-surface rounded-xl border border-line p-6 space-y-4">
            <div className="p-4 rounded-xl border border-sage bg-sage-bg space-y-3">
              <p className="text-sm font-semibold text-sage">
                Save your MCP API Key — it won't be shown again
              </p>
              <p className="text-xs text-ink-secondary">
                AI agents (Claude, Cursor, ChatGPT) use this key to connect to
                your MCP endpoint.
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
              onClick={() => navigate({ to: "/" })}
              className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                         hover:bg-terra-hover active:scale-[0.98] transition-all"
            >
              Continue to Dashboard
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
            {`Welcome to ${appName}`}
          </h1>
          <p className="text-sm text-ink-muted mt-1">
            Create your admin account to get started
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
              Username
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
              Email{" "}
              <span className="text-ink-faint font-normal">
                (optional — for password recovery)
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
              placeholder="admin@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              Password
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
              placeholder="Min. 8 characters"
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-ink mb-1.5"
            >
              Confirm Password
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
              placeholder="Re-enter password"
            />
            {confirmPassword && !passwordsMatch && (
              <p className="text-xs text-rust mt-1">Passwords do not match</p>
            )}
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                       hover:bg-terra-hover active:scale-[0.98] transition-all
                       disabled:opacity-50 disabled:pointer-events-none"
          >
            {loading ? "Creating account…" : "Create Admin Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
