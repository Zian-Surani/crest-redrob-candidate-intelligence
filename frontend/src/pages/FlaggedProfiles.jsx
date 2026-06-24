import { motion } from "framer-motion";
import DataState from "../components/DataState";
import { useApi } from "../hooks/useApi";
import { initials } from "../lib/api";

export default function FlaggedProfiles() {
  const { data, loading, error } = useApi("/flagged", { count: 0, items: [] });
  return (
    <div className="max-w-[1200px] w-full mx-auto pb-12">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-headline font-bold text-slate-900 mb-1">
            Flagged Profiles
          </h1>
          <p className="text-slate-500">
            Transparent evidence for temporal impossibilities, unsupported
            expertise, and skill stuffing.
          </p>
        </div>
        <div className="bg-danger/10 text-danger rounded-2xl px-4 py-3">
          <span className="text-2xl font-bold">{data?.count || 0}</span>
          <span className="text-xs font-bold ml-2">removed</span>
        </div>
      </div>
      <DataState loading={loading} error={error}>
        {(data?.items || []).length ? (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
            className="space-y-4"
          >
            {data.items.map((candidate) => (
              <motion.article
                key={candidate.candidate_id}
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-6 flex items-start space-x-4"
              >
                <div className="w-11 h-11 rounded-2xl bg-danger/10 text-danger flex items-center justify-center text-xs font-bold shrink-0">
                  {initials(candidate.name)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900">
                        {candidate.name}
                      </h3>
                      <p className="text-xs text-slate-500">
                        {candidate.role} · {candidate.candidate_id}
                      </p>
                    </div>
                    <span className="text-xs font-bold text-danger bg-danger/10 px-2.5 py-1 h-fit rounded-md">
                      Risk {(candidate.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-4 space-y-2">
                    {candidate.flags.map((flag, index) => (
                      <p
                        key={index}
                        className="text-sm text-slate-600 bg-slate-50 border border-slate-100 p-3 rounded-xl"
                      >
                        <span className="font-bold text-danger capitalize mr-2">
                          {flag.severity}
                        </span>
                        {flag.evidence}
                      </p>
                    ))}
                  </div>
                </div>
              </motion.article>
            ))}
          </motion.div>
        ) : (
          <div className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-12 text-center">
            <span className="material-symbols-outlined text-success text-5xl">
              verified
            </span>
            <h2 className="text-xl font-bold text-slate-900 mt-3">
              No severe flags in this run
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              Run the full 100K candidate pool to exercise the honeypot
              detector.
            </p>
          </div>
        )}
      </DataState>
    </div>
  );
}
