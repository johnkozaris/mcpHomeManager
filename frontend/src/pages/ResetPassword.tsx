import { useState } from "react";
import { Link, useSearch } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { parseApiError } from "@/lib/utils";
import { Home, ArrowLeft } from "lucide-react";

export function ResetPassword() {
  const { token } = useSearch({ from: "/reset-password" });

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const passwordsMatch = password === confirmPassword;
  const passwordValid = password.length >= 8;
  const canSubmit = token && passwordValid && passwordsMatch && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setLoading(true);

    try {
      await api.auth.resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      setError(parseApiError(err, "Password reset failed"));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <p className="text-sm text-rust mb-4">
            Invalid or missing reset token.
          </p>
          <Link
            to="/login"
            className="text-sm font-medium text-terra hover:text-terra-light transition-colors"
          >
            Back to sign in
          </Link>
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
            {success ? "Password Reset" : "Set New Password"}
          </h1>
        </div>

        <div className="bg-surface rounded-xl border border-line p-6 space-y-4">
          {success ? (
            <div className="text-center space-y-3">
              <p className="text-sm text-ink-secondary">
                Your password has been reset successfully. You can now sign in
                with your new password.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-terra hover:text-terra-light transition-colors"
              >
                <ArrowLeft size={14} /> Sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-rust-bg border border-rust">
                  <div className="w-1.5 h-1.5 rounded-full bg-rust shrink-0" />
                  <p className="text-sm text-rust">{error}</p>
                </div>
              )}

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-ink mb-1.5"
                >
                  New Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  autoFocus
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
                  <p className="text-xs text-rust mt-1">
                    Passwords do not match
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
                {loading ? "Resetting…" : "Reset Password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
