import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useSearchParams } from 'react-router-dom'
import CandidateDrawer from '../components/CandidateDrawer'
import DataState from '../components/DataState'
import { useApi } from '../hooks/useApi'
import { api, apiUrl, inr, initials } from '../lib/api'

const scoreTone = (score) => score >= 75 ? 'text-success' : score >= 55 ? 'text-primary' : 'text-warning'

export default function CandidateManagement() {
  const [params] = useSearchParams()
  const [search, setSearch] = useState(params.get('q') || '')
  const [minimum, setMinimum] = useState(0)
  const [selected, setSelected] = useState(null)
  const [runOpen, setRunOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [actionError, setActionError] = useState('')
  const { data, loading, error, refresh } = useApi('/candidates?page_size=100', { items: [], total: 0 })
  const { data: jobs } = useApi('/jobs', [])
  const { data: dataset } = useApi('/dataset/stats', {})
  const canRunFull = Boolean(dataset?.full_available)

  const visible = useMemo(() => {
    const query = search.trim().toLowerCase()
    return (data?.items || []).filter((candidate) => candidate.score >= minimum && (!query || [candidate.name, candidate.role, candidate.company, candidate.location, candidate.reasoning].join(' ').toLowerCase().includes(query)))
  }, [data, search, minimum])

  const runRanking = async (event) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    if (!canRunFull) {
      setActionError('This hosted sandbox serves the verified 100K full-run snapshot. Candidate-level JD-shift analysis is live; full 100K reranking requires mounting the official candidates.jsonl locally.')
      return
    }
    setRunning(true); setActionError('')
    try {
      await api('/rankings/run', {
        method: 'POST',
        body: JSON.stringify({ job_id: Number(form.get('job_id')), scope: 'full', limit: 100 }),
      })
      setRunOpen(false)
      await refresh()
    } catch (requestError) { setActionError(requestError.message) }
    finally { setRunning(false) }
  }

  return (
    <div className="max-w-[1600px] w-full mx-auto pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <div><h1 className="text-3xl font-headline font-bold text-slate-900 mb-1">Candidate Intelligence</h1><p className="text-slate-500">Ranked by career evidence, skill depth, availability, integrity, and hiring cost.</p></div>
        <div className="flex items-center space-x-3 mt-4 sm:mt-0">
          {data?.ranking_id && <a href={apiUrl(`/rankings/${data.ranking_id}/export.csv`)} className="flex items-center space-x-2 bg-white border border-slate-200 text-slate-700 px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-slate-50 shadow-sm"><span className="material-symbols-outlined text-[18px]">download</span><span>Export CSV</span></a>}
          <button onClick={() => setRunOpen(true)} className="flex items-center space-x-2 bg-primary text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-container shadow-sm hover:shadow-md hover:-translate-y-0.5"><span className="material-symbols-outlined text-[18px]">auto_awesome</span><span>New Ranking</span></button>
        </div>
      </div>

      {actionError && <div className="mb-5 p-4 bg-danger/10 text-danger rounded-2xl text-sm">{actionError}</div>}
      <DataState loading={loading} error={error}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-premium shadow-premium border border-slate-200/60 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center space-x-4 bg-slate-50/50">
            <div className="flex-1 relative"><span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">search</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, role, company, evidence..." className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" /></div>
            <select value={minimum} onChange={(event) => setMinimum(Number(event.target.value))} className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-700"><option value="0">All scores</option><option value="50">50%+</option><option value="65">65%+</option><option value="75">75%+</option></select>
            <div className="hidden sm:block text-sm text-slate-500">Showing <span className="font-medium text-slate-900">{visible.length}</span> candidates</div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead><tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider font-semibold border-b border-slate-100"><th className="px-5 py-4">Rank</th><th className="px-5 py-4">Candidate</th><th className="px-5 py-4">Role & Location</th><th className="px-5 py-4">Match</th><th className="px-5 py-4">Projected CPH</th><th className="px-5 py-4">Availability</th><th className="px-5 py-4 text-right">Analysis</th></tr></thead>
              <tbody className="divide-y divide-slate-100">{visible.map((candidate) => (
                <tr key={candidate.candidate_id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-5 py-4"><span className="text-sm font-bold text-primary">#{candidate.rank}</span></td>
                  <td className="px-5 py-4"><div className="flex items-center space-x-3"><div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">{initials(candidate.name)}</div><div><button onClick={() => setSelected(candidate)} className="font-bold text-slate-900 text-sm group-hover:text-primary text-left">{candidate.name}</button><div className="text-xs text-slate-400 font-mono">{candidate.candidate_id}</div></div></div></td>
                  <td className="px-5 py-4"><div className="font-medium text-slate-800 text-sm">{candidate.role} · {candidate.company}</div><div className="text-xs text-slate-500 mt-0.5"><span className="material-symbols-outlined text-[13px] align-middle mr-1">location_on</span>{candidate.location} · {candidate.years_experience} yrs</div></td>
                  <td className="px-5 py-4"><div className="flex items-center space-x-2"><span className={`font-bold text-sm w-10 ${scoreTone(candidate.score)}`}>{candidate.score.toFixed(1)}</span><div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-primary rounded-full" style={{ width: `${candidate.score}%` }} /></div></div></td>
                  <td className="px-5 py-4"><p className={`text-sm font-bold ${candidate.projected_cph_inr <= 110000 ? 'text-success' : 'text-warning'}`}>{inr(candidate.projected_cph_inr, true)}</p><p className="text-[10px] text-slate-400">benchmark ₹1.1L</p></td>
                  <td className="px-5 py-4"><span className={`inline-flex px-2.5 py-1 rounded-md text-xs font-semibold ${candidate.open_to_work ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>{candidate.behavioral.availability_score}%</span></td>
                  <td className="px-5 py-4 text-right"><button onClick={() => setSelected(candidate)} className="text-primary font-bold text-xs bg-primary/10 hover:bg-primary/20 px-3 py-2 rounded-xl">View evidence</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          {!visible.length && <div className="p-12 text-center text-sm text-slate-500">No candidates match the current filters.</div>}
        </motion.div>
      </DataState>

      {selected && <CandidateDrawer candidate={selected} onClose={() => setSelected(null)} />}
      {runOpen && (
        <div className="fixed inset-0 z-[110] bg-slate-900/30 backdrop-blur-sm flex items-center justify-center p-6">
          <form onSubmit={runRanking} className="bg-white rounded-premium shadow-2xl border border-slate-200 w-full max-w-md p-7">
            <div className="flex justify-between mb-6"><div><h2 className="text-xl font-bold text-slate-900">Run candidate ranking</h2><p className="text-sm text-slate-500 mt-1">The full run streams all 100,000 official profiles when the raw JSONL is mounted locally.</p></div><button type="button" onClick={() => setRunOpen(false)}><span className="material-symbols-outlined text-slate-400">close</span></button></div>
            <label className="block text-xs font-bold text-slate-600 mb-2">Job description</label><select name="job_id" required className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-3 text-sm mb-4">{(jobs || []).map((job) => <option key={job.id} value={job.id}>{job.title} · {job.company}</option>)}</select>
            <div className="mb-5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">{canRunFull ? 'Official 100K candidates.jsonl is mounted. A rerun will execute the full deterministic pipeline.' : 'Hosted mode serves the verified 100K full-run ranking snapshot, not placeholder data. Candidate-level JD shift works live; full rerun locally after mounting the official candidates.jsonl.'}</div>
            <button disabled={running || !jobs?.length || !canRunFull} className="w-full bg-primary text-white rounded-xl py-3 text-sm font-bold disabled:opacity-50">{running ? 'Ranking candidates…' : 'Run full evidence pipeline'}</button>
          </form>
        </div>
      )}
    </div>
  )
}

