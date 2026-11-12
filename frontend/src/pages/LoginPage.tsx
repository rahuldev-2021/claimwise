import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { ThemeToggleIcon } from "../components/ThemeToggleIcon";

export function LoginPage() {
  const { login, user, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (!loading && user) {
    return <Navigate to={from} replace />;
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Sign in failed";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-base px-4 py-10">
      <div className="absolute right-4 top-4 z-10">
        <ThemeToggleIcon />
      </div>

      <header className="mb-8 text-center">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-surface ring-1 ring-border">
          <img src="/favicon.png" alt="" className="h-6 w-6 object-contain" width={24} height={24} />
        </div>
        <p className="mt-4 text-[13px] font-semibold tracking-wide text-text">CLAIMWISE</p>
      </header>

      <div className="w-full max-w-[400px] rounded-2xl border border-border bg-surface p-8 shadow-composer">
        <h1 className="text-xl font-semibold tracking-tight text-text">Sign in</h1>
        <p className="mt-1 text-[13px] text-text-muted">Enter your credentials to continue</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <label className="block text-[13px] font-medium text-text">
            Email
            <span className="relative mt-1.5 flex items-center">
              <Mail className="pointer-events-none absolute left-3 h-4 w-4 text-text-faint" aria-hidden />
              <input
                type="email"
                autoComplete="email"
                required
                className="ui-input w-full py-2.5 pl-10"
                placeholder="Enter email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </span>
          </label>

          <label className="block text-[13px] font-medium text-text">
            Password
            <span className="relative mt-1.5 flex items-center">
              <Lock className="pointer-events-none absolute left-3 h-4 w-4 text-text-faint" aria-hidden />
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                className="ui-input w-full py-2.5 pl-10 pr-10"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="absolute right-2 rounded-md p-1.5 text-text-faint hover:bg-surface-hover hover:text-text"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </span>
          </label>

          {error ? (
            <p className="rounded-lg border border-status-err/30 bg-status-err/10 px-3 py-2 text-[13px] text-status-err">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-accent py-2.5 text-[13px] font-semibold text-accent-fg transition hover:bg-accent-hover disabled:opacity-60"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
