import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export default function Register() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const result = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(form.entries())),
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
      <div className="hidden lg:flex flex-1 relative bg-slate-900 items-center justify-center overflow-hidden">
        <div className="absolute inset-0 opacity-40 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-accent/40 via-slate-900 to-slate-900" />
        <div className="relative z-10 max-w-lg text-center px-12">
          <div className="bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
            <span className="material-symbols-outlined text-4xl text-accent mb-4">
              rocket_launch
            </span>
            <h3 className="text-2xl font-bold text-white mb-4">
              Build your evidence workspace
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed">
              The local SaaS shell stores your account and job history in
              SQLite. Candidate ranking remains offline and reproducible.
            </p>
          </div>
        </div>
      </div>
      <div className="flex-1 flex flex-col justify-center px-12 sm:px-24 lg:px-32 bg-white shadow-2xl">
        <div className="w-full max-w-md mx-auto">
          <Link to="/" className="flex items-center space-x-3 mb-10">
            <div className="w-8 h-8 bg-primary rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">C</span>
            </div>
            <span className="font-bold text-xl text-slate-900">CREST</span>
          </Link>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">
            Create an account
          </h2>
          <p className="text-slate-500 mb-7">
            Set up your workspace and start ranking candidates.
          </p>
          {error && (
            <div className="p-3 rounded-xl bg-danger/10 text-danger text-sm mb-4">
              {error}
            </div>
          )}
          <form onSubmit={submit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field name="first_name" label="First Name" />
              <Field name="last_name" label="Last Name" />
            </div>
            <Field name="email" type="email" label="Work Email" />
            <Field name="company" label="Company" />
            <Field
              name="password"
              type="password"
              minLength="8"
              label="Password"
            />
            <button
              disabled={busy}
              className="w-full bg-slate-900 text-white rounded-xl py-3.5 text-sm font-medium disabled:opacity-50"
            >
              {busy ? "Creating workspace…" : "Get Started"}
            </button>
          </form>
          <div className="mt-7 text-center text-sm text-slate-500">
            Already registered?{" "}
            <Link to="/login" className="font-medium text-primary">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
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
