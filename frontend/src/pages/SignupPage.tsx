import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { register } from "../features/auth/api";

function SignupPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await register({
        username,
        email: email || undefined,
        password,
      });

      navigate("/login");
    } catch {
      setError(
        "Unable to create account. Please check your details.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f7f8] px-4 py-8 text-slate-900 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center justify-center">
        <div className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.10)] lg:grid-cols-[1.05fr_0.95fr]">
          {/* Brand panel */}
          <section className="relative hidden overflow-hidden bg-slate-950 px-10 py-12 text-white lg:flex lg:min-h-[720px] lg:flex-col lg:justify-between xl:px-14">
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
                  Built for your knowledge
                </p>

                <h2 className="text-4xl font-semibold leading-tight tracking-[-0.03em] xl:text-5xl">
                  Start building
                  <br />
                  smarter conversations.
                </h2>

                <p className="mt-6 max-w-md text-base leading-7 text-slate-400">
                  Create your workspace and bring AI conversations and
                  document knowledge together in one place.
                </p>
              </div>
            </div>

            <div className="relative max-w-md space-y-3">
              <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sm font-semibold">
                  01
                </div>

                <div>
                  <p className="text-sm font-semibold">
                    Create your workspace
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">
                    Set up your personal OmniChat account.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sm font-semibold">
                  02
                </div>

                <div>
                  <p className="text-sm font-semibold">
                    Upload your knowledge
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">
                    Add documents and make them searchable.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sm font-semibold">
                  03
                </div>

                <div>
                  <p className="text-sm font-semibold">
                    Ask and explore
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">
                    Get answers grounded in your documents.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Signup panel */}
          <section className="flex min-h-[650px] items-center px-6 py-10 sm:px-10 lg:min-h-[720px] xl:px-14">
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
                  Get started
                </p>

                <h1 className="text-3xl font-semibold tracking-[-0.025em] text-slate-950">
                  Create your account
                </h1>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Set up your OmniChat workspace in just a few seconds.
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
                    placeholder="Choose a username"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10"
                  />
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Email
                    <span className="ml-2 text-xs font-normal text-slate-400">
                      Optional
                    </span>
                  </label>

                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => {
                      setEmail(event.target.value);
                      if (error) {
                        setError("");
                      }
                    }}
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Password
                  </label>

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
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10"
                  />

                  <p className="mt-2 text-xs text-slate-400">
                    Use at least 8 characters for your password.
                  </p>
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
                      Creating account...
                    </>
                  ) : (
                    "Create account"
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
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 transition hover:decoration-slate-950"
                >
                  Sign in
                </Link>
              </p>

              <p className="mt-8 text-center text-xs leading-5 text-slate-400">
                Your account gives you access to your private conversations
                and uploaded knowledge.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

export default SignupPage;