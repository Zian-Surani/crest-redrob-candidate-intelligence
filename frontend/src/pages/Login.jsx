import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export default function Login() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const result = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          password: form.get("password"),
        }),
      });
      localStorage.setItem("crest_token", result.token);
      navigate("/dashboard");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="min-h-screen flex bg-slate-50 font-body">
      <div className="flex-1 flex flex-col justify-center px-12 sm:px-24 lg:px-32 bg-white relative z-10 shadow-2xl">
        <div className="w-full max-w-md mx-auto">
          <Brand />
          <h2 className="text-3xl font-headline font-bold text-slate-900 mb-2">
            Welcome back
          </h2>
          <p className="text-slate-500 mb-8">
            Enter your credentials to access the evidence dashboard.
          </p>
          {error && (
            <div className="p-3 rounded-xl bg-danger/10 text-danger text-sm mb-5">
              {error}
            </div>
          )}
          <form onSubmit={submit} className="space-y-5">
            <Field
              name="email"
              type="email"
              label="Work Email"
              placeholder="name@company.com"
            />
            <Field
              name="password"
              type="password"
              label="Password"
              placeholder="••••••••"
            />
            <button
              disabled={busy}
              className="w-full bg-slate-900 text-white rounded-xl py-3.5 text-sm font-medium hover:bg-slate-800 shadow-sm disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Sign In to CREST"}
            </button>
          </form>
          <div className="mt-8 text-center text-sm text-slate-500">
            No account?{" "}
            <Link to="/register" className="font-medium text-primary">
              Create your workspace
            </Link>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            className="w-full mt-4 text-xs font-bold text-slate-400 hover:text-primary"
          >
            Continue in local demo mode
          </button>
        </div>
      </div>
      <Visual />
    </div>
  );
}
function Brand() {
  return (
    <Link to="/" className="flex items-center space-x-3 mb-12">
      <img src="/favicon.svg" alt="CREST" className="w-8 h-8 object-contain drop-shadow-sm" />
      <span className="font-headline font-bold text-xl tracking-tight text-slate-900">
        CREST
      </span>
    </Link>
  );
}
function Field({ label, ...props }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">
        {label}
      </span>
      <input
        required
        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        {...props}
      />
    </label>
  );
}
function Visual() {
  return (
    <div className="hidden lg:flex flex-1 relative bg-slate-900 items-center justify-center overflow-hidden">
      <div className="absolute inset-0 opacity-40 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/40 via-slate-900 to-slate-900" />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 max-w-lg text-center px-12"
      >
        <div className="bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          <span className="material-symbols-outlined text-4xl text-primary mb-4">
            insights
          </span>
          <h3 className="text-2xl font-bold text-white mb-4">
            Recruitment decisions, with evidence
          </h3>
          <p className="text-slate-300 leading-relaxed text-sm">
            Rank career trajectory, validate profile integrity, forecast
            cost-to-hire, and explain every decision without a hosted LLM.
          </p>
        </div>
      </motion.div>
    </div>
  );
}
