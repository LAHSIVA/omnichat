import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../features/auth/useAuth";

function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await login({
        username,
        password,
      });

      navigate("/app");
    } catch {
      setError("Invalid username or password.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f7f8] px-4 py-8 text-slate-900 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center justify-center">
        <div className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.10)] lg:grid-cols-[1.05fr_0.95fr]">
          {/* Brand panel */}
          <section className="relative hidden overflow-hidden bg-slate-950 px-10 py-12 text-white lg:flex lg:min-h-[680px] lg:flex-col lg:justify-between xl:px-14">
            <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/[0.04]" />
            <div className="absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-white/[0.03]" />

            <div className="relative">
              <div className="mb-8 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-lg font-bold text-slate-950 shadow-lg">
                  O
                </div>

                <div>
                  <p className="text-lg font-semibold tracking-tight">
                    OmniChat
                  </p>
                  <p className="text-xs text-slate-400">
                    AI Workspace
                  </p>
                </div>
              </div>

              <div className="max-w-md">
                <p className="mb-4 text-sm font-medium uppercase tracking-[0.18em] text-slate-400">
                  Intelligent conversations
                </p>

                <h2 className="text-4xl font-semibold leading-tight tracking-[-0.03em] xl:text-5xl">
                  Your knowledge.
                  <br />
                  One conversation.
                </h2>

                <p className="mt-6 max-w-md text-base leading-7 text-slate-400">
                  Chat with AI, explore your documents, and keep your
                  conversations organized in one focused workspace.
                </p>
              </div>
            </div>

            <div className="relative grid max-w-md grid-cols-3 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <p className="text-sm font-semibold">AI Chat</p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Natural conversations
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <p className="text-sm font-semibold">RAG</p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Ask your documents
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <p className="text-sm font-semibold">History</p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Continue anytime
                </p>
              </div>
            </div>
          </section>

          {/* Login panel */}
          <section className="flex min-h-[600px] items-center px-6 py-10 sm:px-10 lg:min-h-[680px] xl:px-14">
            <div className="mx-auto w-full max-w-md">
              {/* Mobile branding */}
              <div className="mb-10 flex items-center gap-3 lg:hidden">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white">
                  O
                </div>

                <div>
                  <p className="font-semibold tracking-tight">
                    OmniChat
                  </p>
                  <p className="text-xs text-slate-500">
                    AI Workspace
                  </p>
                </div>
              </div>

              <div className="mb-8">
                <p className="mb-3 text-sm font-medium text-slate-500">
                  Welcome back
                </p>

                <h1 className="text-3xl font-semibold tracking-[-0.025em] text-slate-950">
                  Sign in to OmniChat
                </h1>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Continue your conversations and access your knowledge
                  workspace.
                </p>
              </div>

              <form
                onSubmit={handleSubmit}
                className="space-y-5"
              >
                <div>
                  <label
                    htmlFor="username"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Username
                  </label>

                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(event) => {
                      setUsername(event.target.value);
                      if (error) {
                        setError("");
                      }
                    }}
                    required
                    autoComplete="username"
                    autoFocus
                    placeholder="Enter your username"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10"
                  />
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label
                      htmlFor="password"
                      className="block text-sm font-medium text-slate-700"
                    >
                      Password
                    </label>
                  </div>

                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      if (error) {
                        setError("");
                      }
                    }}
                    required
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10"
                  />
                </div>

                {error && (
                  <div
                    role="alert"
                    className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-0.5 font-semibold"
                    >
                      !
                    </span>

                    <p>{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex h-12 w-full items-center justify-center rounded-xl bg-slate-950 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-4 focus:ring-slate-900/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? (
                    <>
                      <span
                        aria-hidden="true"
                        className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
                      />
                      Signing in...
                    </>
                  ) : (
                    "Sign in"
                  )}
                </button>
              </form>

              <div className="my-8 flex items-center gap-4">
                <div className="h-px flex-1 bg-slate-200" />
                <span className="text-xs text-slate-400">
                  OR
                </span>
                <div className="h-px flex-1 bg-slate-200" />
              </div>

              <p className="text-center text-sm text-slate-500">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 transition hover:decoration-slate-950"
                >
                  Create one
                </Link>
              </p>

              <p className="mt-8 text-center text-xs leading-5 text-slate-400">
                By continuing, you agree to use OmniChat responsibly and
                securely.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

export default LoginPage;