import { useState } from 'react'
import { api, inr, initials } from '../lib/api'

const componentLabels = {
  career_fit: 'Career fit', skill_depth: 'Skill depth', experience_fit: 'Experience band',
  location_fit: 'Location fit', external_validation: 'External validation',
}

export default function CandidateDrawer({ candidate, onClose }) {
  const [tab, setTab] = useState('analysis')
  const [shiftOpen, setShiftOpen] = useState(false)
  const [shiftResult, setShiftResult] = useState(null)
  const [questions, setQuestions] = useState(candidate?.interview_questions || [])
  const [reasoningAudit, setReasoningAudit] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  if (!candidate) return null

  const runShift = async (event) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusy(true); setError('')
    try {
      const result = await api(`/candidates/${candidate.candidate_id}/evaluate-shift`, {
        method: 'POST',
        body: JSON.stringify({
          title: form.get('title'), location: form.get('location'), description: form.get('description'),
          salary_min_lpa: Number(form.get('salary_min_lpa')), salary_max_lpa: Number(form.get('salary_max_lpa')),
        }),
      })
      setShiftResult(result)
    } catch (requestError) { setError(requestError.message) }
    finally { setBusy(false) }
  }

  const askOllama = async () => {
    setBusy(true); setError('')
    try {
      const result = await api(`/candidates/${candidate.candidate_id}/interview-questions`, {
        method: 'POST', body: JSON.stringify({ use_ollama: true }),
      })
      setQuestions(result.questions)
    } catch (requestError) { setError(requestError.message) }
    finally { setBusy(false) }
  }

  const auditWithQwen = async () => {
    setBusy(true); setError('')
    try {
      const result = await api(`/candidates/${candidate.candidate_id}/reasoning-audit`, {
        method: 'POST', body: JSON.stringify({ use_ollama: true }),
      })
      setReasoningAudit(result)
    } catch (requestError) { setError(requestError.message) }
    finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      <button aria-label="Close candidate analysis" onClick={onClose} className="absolute inset-0 bg-slate-900/25 backdrop-blur-sm" />
      <aside className="relative w-full max-w-2xl h-full bg-slate-50 shadow-2xl overflow-y-auto animate-slide-in-right">
        <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-xl border-b border-slate-200 px-7 py-5">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center font-bold">{initials(candidate.name)}</div>
              <div>
                <div className="flex items-center space-x-2"><span className="text-xs font-bold text-primary">#{candidate.rank}</span><h2 className="text-xl font-bold text-slate-900">{candidate.name}</h2></div>
                <p className="text-sm text-slate-500">{candidate.role} · {candidate.company}</p>
              </div>
            </div>
            <button onClick={onClose} className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center"><span className="material-symbols-outlined">close</span></button>
          </div>
          <div className="flex mt-5 space-x-2">
            {['analysis', 'evidence', 'interview'].map((item) => (
              <button key={item} onClick={() => setTab(item)} className={`px-4 py-2 rounded-xl text-xs font-bold capitalize transition-colors ${tab === item ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>{item}</button>
            ))}
          </div>
        </div>

        <div className="p-7 space-y-6">
          {error && <div className="p-4 rounded-2xl bg-danger/10 text-danger text-sm">{error}</div>}
          {tab === 'analysis' && (
            <>
              <div className="grid grid-cols-3 gap-4">
                <Metric label="Match score" value={`${candidate.score.toFixed(1)}%`} tone="text-primary" />
                <Metric label="Projected CPH" value={inr(candidate.projected_cph_inr, true)} tone={candidate.projected_cph_inr <= 110000 ? 'text-success' : 'text-warning'} />
                <Metric label="Availability" value={`${candidate.behavioral.availability_score}%`} tone="text-accent" />
              </div>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <h3 className="font-bold text-slate-900 mb-2">Why this rank</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{candidate.reasoning}</p>
                {candidate.semantic_relevance?.enabled && <div className="mt-4 flex items-center justify-between bg-primary/5 border border-primary/10 rounded-xl p-3"><div><p className="text-xs font-bold text-primary">Hybrid semantic retrieval</p><p className="text-[10px] text-slate-500 mt-1">Retrieval signal only; explanation remains evidence-derived.</p></div><span className="text-lg font-bold text-primary">{candidate.semantic_relevance.similarity}%</span></div>}
              </section>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6 space-y-4">
                <div className="flex justify-between"><h3 className="font-bold text-slate-900">Score breakdown</h3><span className="text-xs font-mono text-slate-400">deterministic · score-derived</span></div>
                {Object.entries(candidate.components).map(([key, value]) => {
                  const maximum = candidate.component_max[key]
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1.5"><span className="font-medium text-slate-600">{componentLabels[key]}</span><span className="font-bold text-slate-900">{value.toFixed(1)} / {maximum}</span></div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(100, value / maximum * 100)}%` }} /></div>
                    </div>
                  )
                })}
              </section>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <div className="flex justify-between items-center mb-4"><h3 className="font-bold text-slate-900">Cost-to-hire forecast</h3><span className={`text-xs font-bold px-2 py-1 rounded-md ${candidate.cph_breakdown.savings_vs_benchmark >= 0 ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>{candidate.cph_breakdown.savings_vs_benchmark >= 0 ? `${inr(candidate.cph_breakdown.savings_vs_benchmark, true)} saved` : `${inr(-candidate.cph_breakdown.savings_vs_benchmark, true)} over benchmark`}</span></div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <Cost label="Recruiter coordination" value={candidate.cph_breakdown.recruiter_coordination} />
                  <Cost label="Vacancy delay" value={candidate.cph_breakdown.vacancy_delay} />
                  <Cost label="Drop-off risk" value={candidate.cph_breakdown.dropout_risk} />
                  <Cost label="Salary mismatch" value={candidate.cph_breakdown.salary_mismatch} />
                </div>
              </section>
              <button onClick={() => setShiftOpen((value) => !value)} className="w-full bg-slate-900 text-white rounded-xl py-3 text-sm font-bold hover:bg-slate-800 transition-colors flex items-center justify-center space-x-2"><span className="material-symbols-outlined text-[18px]">swap_horiz</span><span>Evaluate for a different role</span></button>
              {shiftOpen && (
                <form onSubmit={runShift} className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6 space-y-4">
                  <div><h3 className="font-bold text-slate-900">JD Shift analysis</h3><p className="text-xs text-slate-500 mt-1">Rescore this candidate only and show the decision delta.</p></div>
                  <div className="grid grid-cols-2 gap-3">
                    <input name="title" required placeholder="Alternative job title" className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm" />
                    <input name="location" required defaultValue="India" placeholder="Location" className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm" />
                    <input name="salary_min_lpa" type="number" defaultValue="20" className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm" />
                    <input name="salary_max_lpa" type="number" defaultValue="40" className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm" />
                  </div>
                  <textarea name="description" required minLength="40" rows="6" placeholder="Paste the alternative job description…" className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm resize-none" />
                  <button disabled={busy} className="bg-primary text-white rounded-xl px-5 py-2.5 text-sm font-bold disabled:opacity-50">{busy ? 'Evaluating…' : 'Compare fit'}</button>
                  {shiftResult && <div className="grid grid-cols-2 gap-3 pt-2"><Metric label="New score" value={`${shiftResult.score.toFixed(1)}%`} tone="text-primary" /><Metric label="Score delta" value={`${shiftResult.score_delta > 0 ? '+' : ''}${shiftResult.score_delta}`} tone={shiftResult.score_delta >= 0 ? 'text-success' : 'text-danger'} /></div>}
                </form>
              )}
            </>
          )}

          {tab === 'evidence' && (
            <>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <h3 className="font-bold text-slate-900 mb-4">JD requirement evidence</h3>
                <div className="space-y-3">{candidate.matched_requirements.map((item) => <Requirement key={item.requirement} item={item} />)}</div>
              </section>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <div className="flex justify-between items-center mb-4"><h3 className="font-bold text-slate-900">Integrity check</h3><span className={`text-xs font-bold px-2 py-1 rounded-md ${candidate.integrity.passed ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>{candidate.integrity.passed ? 'Passed' : 'Flagged'}</span></div>
                {candidate.integrity.flags.length ? candidate.integrity.flags.map((flag, index) => <p key={index} className="text-sm text-danger bg-danger/5 rounded-xl p-3 mb-2">{flag.evidence}</p>) : <p className="text-sm text-slate-500">No temporal impossibility, unsupported expert claim, or skill-stuffing pattern detected.</p>}
              </section>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <h3 className="font-bold text-slate-900 mb-4">Career evidence</h3>
                <div className="space-y-5">{candidate.career_history.map((role, index) => <div key={`${role.company}-${index}`} className="border-l-2 border-primary/20 pl-4"><p className="text-sm font-bold text-slate-900">{role.title} · {role.company}</p><p className="text-xs text-slate-400 mb-2">{role.duration_months} months · {role.industry}</p><p className="text-xs text-slate-600 leading-relaxed">{role.description}</p></div>)}</div>
              </section>
            </>
          )}

          {tab === 'interview' && (
            <>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <div className="flex items-center justify-between mb-5"><div><h3 className="font-bold text-slate-900">Evidence-gap interview</h3><p className="text-xs text-slate-500 mt-1">Qwen 2.5 Coder 7B generates local, grounded questions.</p></div><button disabled={busy} onClick={askOllama} className="text-xs font-bold text-primary bg-primary/10 px-3 py-2 rounded-xl disabled:opacity-50">Use Qwen 7B</button></div>
                <ol className="space-y-4">{questions.map((question, index) => <li key={question} className="flex space-x-3"><span className="w-7 h-7 rounded-lg bg-slate-900 text-white text-xs font-bold flex items-center justify-center shrink-0">{index + 1}</span><p className="text-sm text-slate-600 leading-relaxed">{question}</p></li>)}</ol>
              </section>
              <section className="bg-white rounded-premium border border-slate-200/60 shadow-premium p-6">
                <div className="flex items-start justify-between"><div><h3 className="font-bold text-slate-900">Stage 4 reasoning audit</h3><p className="text-xs text-slate-500 mt-1">Qwen 14B checks the explanation against the supplied profile. Advisory only; it never changes the score or rank.</p></div><button disabled={busy} onClick={auditWithQwen} className="text-xs font-bold text-accent bg-accent/10 px-3 py-2 rounded-xl disabled:opacity-50 shrink-0 ml-4">Audit with Qwen 14B</button></div>
                {reasoningAudit && <div className="mt-5 space-y-3"><div className="flex items-center justify-between bg-slate-50 border border-slate-100 rounded-xl p-3"><span className="text-xs font-bold text-slate-500">Verdict · {reasoningAudit.source}</span><span className={`text-xs font-bold uppercase ${reasoningAudit.audit.verdict === 'pass' ? 'text-success' : reasoningAudit.audit.verdict === 'fail' ? 'text-danger' : 'text-warning'}`}>{reasoningAudit.audit.verdict}</span></div><p className="text-xs text-slate-600 leading-relaxed"><strong>Rank consistency:</strong> {reasoningAudit.audit.rank_consistency}</p><p className="text-xs text-slate-600 leading-relaxed"><strong>Recommendation:</strong> {reasoningAudit.audit.recommendation}</p>{reasoningAudit.audit.unsupported_claims.length > 0 && <div className="bg-danger/5 text-danger text-xs rounded-xl p-3"><strong>Unsupported claims:</strong> {reasoningAudit.audit.unsupported_claims.join('; ')}</div>}{reasoningAudit.audit.missing_concerns.length > 0 && <div className="bg-warning/5 text-warning text-xs rounded-xl p-3"><strong>Missing concerns:</strong> {reasoningAudit.audit.missing_concerns.join('; ')}</div>}<p className="text-[10px] font-mono text-slate-400">Model: {reasoningAudit.audit.model}</p></div>}
              </section>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

function Metric({ label, value, tone }) {
  return <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm"><p className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">{label}</p><p className={`text-xl font-bold ${tone}`}>{value}</p></div>
}
function Cost({ label, value }) {
  return <div className="bg-slate-50 rounded-xl p-3"><p className="text-xs text-slate-500">{label}</p><p className="font-bold text-slate-900">{inr(value)}</p></div>
}
function Requirement({ item }) {
  const tone = item.status === 'exact' ? 'bg-success/10 text-success' : item.status === 'semantic' ? 'bg-primary/10 text-primary' : 'bg-danger/10 text-danger'
  return <div className="border border-slate-100 rounded-2xl p-4"><div className="flex justify-between mb-2"><p className="text-sm font-bold text-slate-900">{item.requirement}</p><span className={`text-[10px] uppercase font-bold px-2 py-1 rounded-md ${tone}`}>{item.status}</span></div><p className="text-xs text-slate-500">{item.evidence}</p></div>
}
