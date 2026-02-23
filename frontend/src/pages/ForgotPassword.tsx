import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { parseApiError } from "@/lib/utils";
import { Home, ArrowLeft } from "lucide-react";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.auth.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(parseApiError(err, "Failed to send reset email"));
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
          <h1 className="text-xl font-semibold text-ink">Reset Password</h1>
          <p className="text-sm text-ink-muted mt-1">
            {sent
              ? "Check your email"
              : "Enter your email to receive a reset link"}
          </p>
        </div>

        <div className="bg-surface rounded-xl border border-line p-6 space-y-4">
          {sent ? (
            <div className="text-center space-y-3">
              <p className="text-sm text-ink-secondary">
                If an account with that email exists, a password reset link has
                been sent. The link expires in 1 hour.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-terra hover:text-terra-light transition-colors"
              >
                <ArrowLeft size={14} /> Back to sign in
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
                  htmlFor="email"
                  className="block text-sm font-medium text-ink mb-1.5"
                >
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  autoFocus
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink text-sm
                             placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-terra/40 focus:border-terra
                             transition-colors"
                  placeholder="you@example.com"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !email}
                className="w-full py-2.5 rounded-lg bg-terra text-white text-sm font-medium
                           hover:bg-terra-hover active:scale-[0.98] transition-all
                           disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? "Sending…" : "Send Reset Link"}
              </button>

              <div className="text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink transition-colors"
                >
                  <ArrowLeft size={14} /> Back to sign in
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
