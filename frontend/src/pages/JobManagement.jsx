import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import DataState from "../components/DataState";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";

export default function JobManagement() {
  const navigate = useNavigate();
  const [createOpen, setCreateOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const { data: jobs, loading, error, refresh } = useApi("/jobs", []);
  const { data: dataset } = useApi("/dataset/stats", {});
  const { data: latest } = useApi("/rankings/latest", {});

  const createJob = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setActionError("");
    try {
      await api("/jobs", {
        method: "POST",
        body: JSON.stringify({
          title: form.get("title"),
          company: form.get("company"),
          location: form.get("location"),
          description: form.get("description"),
          salary_min_lpa: Number(form.get("salary_min_lpa")),
          salary_max_lpa: Number(form.get("salary_max_lpa")),
        }),
      });
      setCreateOpen(false);
      await refresh();
    } catch (requestError) {
      setActionError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const runJob = async (jobId) => {
    setBusy(true);
    setActionError("");
    try {
      await api("/rankings/run", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId, scope: "sample", limit: 50 }),
      });
      navigate("/dashboard/candidates");
    } catch (requestError) {
      setActionError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-[1600px] w-full mx-auto pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <div>
          <h1 className="text-3xl font-headline font-bold text-slate-900 mb-1">
            Job Intelligence
          </h1>
          <p className="text-slate-500">
            Create a JD, verify the parsed hiring signals, and rank the official
            candidate pool.
          </p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="mt-4 sm:mt-0 flex items-center space-x-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-container shadow-sm hover:shadow-md hover:-translate-y-0.5"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          <span>Create Job</span>
        </button>
      </div>
      {actionError && (
        <div className="mb-5 p-4 bg-danger/10 text-danger rounded-2xl text-sm">
          {actionError}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Stat
          label="Active Jobs"
          value={jobs?.length || 0}
          icon="work"
          color="text-primary"
          bg="bg-primary/10"
        />
        <Stat
          label="Candidate Store"
          value={(dataset?.candidate_count || 0).toLocaleString()}
          icon="database"
          color="text-success"
          bg="bg-success/10"
        />
        <Stat
          label="Last Rank Runtime"
          value={`${latest?.duration_seconds || 0}s`}
          icon="timer"
          color="text-accent"
          bg="bg-accent/10"
        />
      </div>
      <DataState loading={loading} error={error}>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {(jobs || []).map((job) => (
            <motion.article
              key={job.id}
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-6 hover:border-primary/30 transition-colors"
            >
              <div className="flex justify-between items-start">
                <span className="inline-flex px-2.5 py-1 rounded-md text-xs font-semibold bg-success/10 text-success">
                  {job.status}
                </span>
                <span className="text-xs text-slate-400">Job #{job.id}</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mt-4">
                {job.title}
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                {job.company} · {job.location}
              </p>
              <div className="flex flex-wrap gap-2 mt-5">
                {job.parsed.required_skills.map((skill) => (
                  <span
                    key={skill}
                    className="text-xs font-medium text-primary bg-primary/10 px-2.5 py-1 rounded-md"
                  >
                    {skill}
                  </span>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3 mt-5 py-4 border-y border-slate-100">
                <Mini
                  label="Experience"
                  value={`${job.parsed.experience_min}–${job.parsed.experience_max} yrs`}
                />
                <Mini
                  label="Notice target"
                  value={`${job.parsed.notice_period_target} days`}
                />
                <Mini
                  label="Requirements"
                  value={job.parsed.required_skills.length}
                />
              </div>
              <div className="flex justify-between items-center mt-5">
                <p className="text-xs text-slate-400">
                  Created {new Date(job.created_at).toLocaleDateString()}
                </p>
                <button
                  disabled={busy}
                  onClick={() => runJob(job.id)}
                  className="bg-slate-900 text-white px-4 py-2.5 rounded-xl text-xs font-bold hover:bg-slate-800 disabled:opacity-50"
                >
                  Rank sample pool
                </button>
              </div>
            </motion.article>
          ))}
        </motion.div>
      </DataState>

      {createOpen && (
        <div className="fixed inset-0 z-[110] bg-slate-900/30 backdrop-blur-sm flex items-center justify-center p-6">
          <form
            onSubmit={createJob}
            className="bg-white rounded-premium shadow-2xl border border-slate-200 w-full max-w-2xl p-7 max-h-[90vh] overflow-y-auto"
          >
            <div className="flex justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  Create evidence-based job
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  CREST extracts requirements; the description remains the
                  source of truth.
                </p>
              </div>
              <button type="button" onClick={() => setCreateOpen(false)}>
                <span className="material-symbols-outlined text-slate-400">
                  close
                </span>
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field
                name="title"
                label="Job title"
                placeholder="Senior AI Engineer"
              />
              <Field name="company" label="Company" defaultValue="Acme Corp" />
              <Field
                name="location"
                label="Location"
                defaultValue="Pune / Noida, India"
              />
              <div className="grid grid-cols-2 gap-2">
                <Field
                  name="salary_min_lpa"
                  label="Min LPA"
                  type="number"
                  defaultValue="20"
                />
                <Field
                  name="salary_max_lpa"
                  label="Max LPA"
                  type="number"
                  defaultValue="40"
                />
              </div>
            </div>
            <label className="block text-xs font-bold text-slate-600 mt-4 mb-2">
              Job description
            </label>
            <textarea
              required
              minLength="40"
              name="description"
              rows="11"
              placeholder="Paste the complete job description, including must-haves, preferred skills, constraints, and logistics…"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
            <button
              disabled={busy}
              className="w-full mt-5 bg-primary text-white rounded-xl py-3 text-sm font-bold disabled:opacity-50"
            >
              {busy ? "Parsing job…" : "Create and parse signals"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, icon, color, bg }) {
  return (
    <div className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-5 flex items-center space-x-4">
      <div
        className={`w-12 h-12 ${bg} ${color} rounded-2xl flex items-center justify-center`}
      >
        <span className="material-symbols-outlined">{icon}</span>
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium">{label}</p>
        <h4 className="text-2xl font-bold text-slate-900">{value}</h4>
      </div>
    </div>
  );
}
function Mini({ label, value }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
        {label}
      </p>
      <p className="text-sm font-bold text-slate-800 mt-1">{value}</p>
    </div>
  );
}
function Field({ label, ...props }) {
  return (
    <label className="block">
      <span className="block text-xs font-bold text-slate-600 mb-2">
        {label}
      </span>
      <input
        required
        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm"
        {...props}
      />
    </label>
  );
}
