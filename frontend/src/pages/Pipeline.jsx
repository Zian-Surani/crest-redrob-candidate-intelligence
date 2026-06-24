import { motion } from "framer-motion";
import DataState from "../components/DataState";
import { useApi } from "../hooks/useApi";
import { inr, initials } from "../lib/api";

const tones = {
  sourced: "bg-slate-100 border-slate-200",
  screened: "bg-accent/10 border-accent/20",
  interview: "bg-primary/10 border-primary/20",
  shortlisted: "bg-success/10 border-success/20",
};

export default function Pipeline() {
  const { data, loading, error } = useApi("/pipeline", {
    stages: [],
    funnel: [],
  });
  return (
    <div className="max-w-[1600px] w-full mx-auto pb-12">
      <div className="mb-7">
        <h1 className="text-3xl font-headline font-bold text-slate-900 mb-1">
          Recruitment Pipeline
        </h1>
        <p className="text-slate-500">
          Evidence pipeline for {data?.job?.title || "the active role"}.
        </p>
      </div>
      <DataState loading={loading} error={error}>
        <div className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6 mb-6">
          <div className="flex justify-between items-center mb-5">
            <div>
              <h3 className="font-bold text-slate-900">Ranking funnel</h3>
              <p className="text-xs text-slate-500 mt-1">
                Every reduction is inspectable—not a black box.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Run #{data?.ranking_id}
            </span>
          </div>
          <div className="grid grid-cols-5 gap-3">
            {(data?.funnel || []).map((stage, index) => (
              <div key={stage.stage} className="relative">
                <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                  <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                    {stage.stage}
                  </p>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {stage.count.toLocaleString()}
                  </p>
                </div>
                {index < data.funnel.length - 1 && (
                  <span className="absolute -right-3 top-1/2 z-10 text-slate-300 material-symbols-outlined text-[16px]">
                    chevron_right
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          className="flex space-x-5 overflow-x-auto pb-4"
        >
          {(data?.stages || []).map((stage) => (
            <motion.section
              key={stage.id}
              variants={{
                hidden: { opacity: 0, x: -15 },
                visible: { opacity: 1, x: 0 },
              }}
              className="flex-shrink-0 w-[285px]"
            >
              <div
                className={`mb-4 px-4 py-3 rounded-2xl border ${tones[stage.id]} flex justify-between items-center`}
              >
                <h3 className="font-bold text-slate-900">{stage.title}</h3>
                <span className="text-xs font-bold bg-white text-slate-700 px-2 py-1 rounded-md shadow-sm">
                  {stage.count}
                </span>
              </div>
              <div className="bg-slate-50/50 border border-slate-100 rounded-3xl p-3 space-y-3 min-h-[420px]">
                {stage.items.map((candidate) => (
                  <article
                    key={candidate.candidate_id}
                    className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200/60 hover:border-primary/30 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary text-[10px] font-bold flex items-center justify-center">
                        {initials(candidate.name)}
                      </div>
                      <div className="min-w-0">
                        <p className="font-bold text-slate-900 text-sm truncate">
                          {candidate.name}
                        </p>
                        <p className="text-[10px] text-slate-400">
                          #{candidate.rank} · {candidate.candidate_id}
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 font-medium mt-3 truncate">
                      {candidate.role} · {candidate.company}
                    </p>
                    <div className="flex justify-between items-center border-t border-slate-100 pt-3 mt-3">
                      <span className="text-xs font-bold text-primary">
                        {candidate.score.toFixed(1)} match
                      </span>
                      <span className="text-xs font-bold text-success">
                        {inr(candidate.projected_cph_inr, true)}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            </motion.section>
          ))}
        </motion.div>
      </DataState>
    </div>
  );
}
