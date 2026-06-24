import DataState from '../components/DataState'
import { useApi } from '../hooks/useApi'

export default function About() {
  const { data, loading, error } = useApi('/about', {})
  const { data: health } = useApi('/health', {})
  return <div className="max-w-[1100px] w-full mx-auto pb-12"><DataState loading={loading} error={error}>
    <div className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-9 mb-6 relative overflow-hidden"><div className="absolute top-0 right-0 w-72 h-72 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" /><span className="text-xs font-bold uppercase tracking-widest text-primary">Candidate Reliability & Evidence-based Scoring Technology</span><h1 className="text-4xl font-headline font-bold text-slate-900 mt-3">{data?.name}</h1><p className="text-lg text-slate-500 mt-3 max-w-2xl leading-relaxed">{data?.promise}</p><div className="flex space-x-3 mt-7"><Badge label={`${health?.dataset?.candidate_count?.toLocaleString() || 0} profiles`} /><Badge label="CPU-only ranking" /><Badge label="23 behavioral signals" /></div></div>
    <div className="grid grid-cols-2 gap-6"><section className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-7"><h2 className="text-xl font-bold text-slate-900 mb-5">Four-layer intelligence</h2><ol className="space-y-4">{(data?.architecture || []).map((item, index) => <li key={item} className="flex items-center space-x-3"><span className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">{index + 1}</span><span className="text-sm font-medium text-slate-700">{item}</span></li>)}</ol></section><section className="bg-white rounded-premium shadow-premium border border-slate-200/60 p-7"><h2 className="text-xl font-bold text-slate-900 mb-5">Engineering principles</h2><ul className="space-y-4">{(data?.principles || []).map((item) => <li key={item} className="flex items-start space-x-3"><span className="material-symbols-outlined text-success text-[20px]">check_circle</span><span className="text-sm text-slate-600 leading-relaxed">{item}</span></li>)}</ul></section></div>
  </DataState></div>
}
function Badge({ label }) { return <span className="text-xs font-bold text-slate-600 bg-slate-50 border border-slate-100 px-3 py-2 rounded-xl">{label}</span> }
