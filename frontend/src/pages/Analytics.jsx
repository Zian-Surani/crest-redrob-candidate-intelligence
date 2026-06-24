import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts'
import DataState from '../components/DataState'
import { useApi } from '../hooks/useApi'
import { apiUrl, inr } from '../lib/api'

const COLORS = ['#2563EB', '#7C3AED', '#10B981', '#F59E0B', '#64748B', '#EF4444']
const TABS = [
  ['overview', 'Run Overview'],
  ['quality', 'Candidate Quality'],
  ['cost', 'Cost & Hireability'],
  ['readiness', 'Hackathon Readiness'],
]

export default function Analytics() {
  const [tab, setTab] = useState('overview')
  const { data, loading, error } = useApi('/analytics/overview', {})

  return <div className="max-w-[1600px] w-full mx-auto pb-12">
    <div className="flex justify-between items-start mb-7">
      <div>
        <h1 className="text-3xl font-headline font-bold text-slate-900 mb-1">Recruitment & Submission Analytics</h1>
        <p className="text-slate-500">Recruiter decisions, pipeline quality, operational proof, and official challenge readiness.</p>
      </div>
      {data?.ranking_id && <a href={apiUrl(`/rankings/${data.ranking_id}/export.csv`)} className="flex items-center space-x-2 bg-white border border-slate-200 text-slate-700 px-4 py-2.5 rounded-xl text-sm font-bold hover:bg-slate-50 shadow-sm"><span className="material-symbols-outlined text-[18px]">download</span><span>Export Top 100</span></a>}
    </div>

    <div className="inline-flex bg-white border border-slate-200/60 shadow-sm rounded-2xl p-1.5 mb-7">
      {TABS.map(([id, label]) => <button key={id} onClick={() => setTab(id)} className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-colors ${tab === id ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-50'}`}>{label}</button>)}
    </div>

    <DataState loading={loading} error={error}>
      <motion.div key={tab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        {tab === 'overview' && <Overview data={data} />}
        {tab === 'quality' && <Quality data={data} />}
        {tab === 'cost' && <Cost data={data} />}
        {tab === 'readiness' && <Readiness data={data} />}
      </motion.div>
    </DataState>
  </div>
}

function Overview({ data }) {
  const top = data?.top_candidate || {}
  const stability = data?.top_rank_stability || {}
  return <div className="space-y-6">
    <section className="bg-slate-900 text-white rounded-premium shadow-premium p-7 relative overflow-hidden">
      <div className="absolute right-0 top-0 w-80 h-80 rounded-full bg-primary/20 blur-3xl -translate-y-1/2 translate-x-1/3" />
      <div className="relative flex justify-between items-center">
        <div><p className="text-xs uppercase tracking-[0.18em] font-bold text-blue-300">Corrected persisted full run</p><h2 className="text-2xl font-bold mt-2">{(data?.candidate_count || 0).toLocaleString()} processed · {(data?.integrity_flags_count || 0).toLocaleString()} high-risk excluded · {data?.shortlist_count || 0} ranked</h2><p className="text-sm text-slate-300 mt-2">Completed in {data?.runtime_seconds || 0}s. Rank 1 remains {top.name || top.candidate_id || 'unavailable'} across {stability.stable_full_runs || 0} of {stability.full_runs || 0} persisted full runs.</p></div>
        <div className="text-right shrink-0 ml-8"><p className="text-4xl font-bold text-white">{stability.rate || 0}%</p><p className="text-xs text-blue-200 mt-1">top-rank stability</p></div>
      </div>
    </section>

    <div className="grid grid-cols-4 gap-6">
      <Kpi label="Candidates evaluated" value={(data?.candidate_count || 0).toLocaleString()} note="Official JSONL pool" icon="groups" tone="text-primary bg-primary/10" />
      <Kpi label="Integrity exclusions" value={(data?.integrity_flags_count || 0).toLocaleString()} note={`${data?.integrity_removal_rate || 0}% of pool`} icon="shield" tone="text-warning bg-warning/10" />
      <Kpi label="Ranking runtime" value={`${data?.runtime_seconds || 0}s`} note={`${data?.runtime_budget_used_percent || 0}% of 5-minute budget`} icon="speed" tone="text-accent bg-accent/10" />
      <Kpi label="Throughput" value={`${(data?.throughput_candidates_per_second || 0).toLocaleString()}/s`} note="CPU-only, network off" icon="memory" tone="text-success bg-success/10" />
    </div>

    <Instruction title="How a recruiter should read this page" steps={[
      'Start with integrity removals: suspicious profiles never enter the final top-K.',
      'Inspect the funnel to see where candidates lost relevance or availability.',
      'Use score bands and location mix to assess shortlist depth—not only rank 1.',
      'Open Candidate Quality for evidence coverage, behavior, notice, and reasoning checks.',
      'Use Cost & Hireability before deciding whom to contact first.',
    ]} />

    <div className="grid grid-cols-3 gap-6">
      <ChartCard className="col-span-2" title="Ranking run history" subtitle="Average match across persisted sample and full runs.">
        <ResponsiveContainer width="100%" height="100%"><AreaChart data={data?.history || []}><defs><linearGradient id="runScore" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563EB" stopOpacity={0.3}/><stop offset="95%" stopColor="#2563EB" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0"/><XAxis dataKey="name" axisLine={false} tickLine={false}/><YAxis domain={[0, 100]} axisLine={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle}/><Area type="monotone" dataKey="score" stroke="#2563EB" strokeWidth={3} fill="url(#runScore)"/></AreaChart></ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Score quality bands" subtitle="Composition of the final shortlist.">
        <Donut data={data?.score_distribution || []} />
      </ChartCard>
    </div>

    <div className="grid grid-cols-2 gap-6">
      <ChartCard title="Decision funnel" subtitle="Remaining candidates after each ranking layer.">
        <ResponsiveContainer width="100%" height="100%"><BarChart data={data?.pipeline || []} layout="vertical" margin={{ left: 38 }}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" axisLine={false} tickLine={false}/><YAxis type="category" dataKey="stage" axisLine={false} tickLine={false} width={120} fontSize={11}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="count" fill="#7C3AED" radius={[0, 8, 8, 0]} barSize={22}/></BarChart></ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Shortlist locations" subtitle="Geographic distribution of the top 100.">
        <ResponsiveContainer width="100%" height="100%"><BarChart data={data?.location_distribution || []}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" axisLine={false} tickLine={false} fontSize={10}/><YAxis axisLine={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="value" fill="#10B981" radius={[8, 8, 0, 0]}/></BarChart></ResponsiveContainer>
      </ChartCard>
    </div>

    <ProductActivity data={data?.product_activity} />
  </div>
}

function Quality({ data }) {
  const reasoning = data?.reasoning_quality || {}
  const semantic = data?.semantic_retrieval || {}
  return <div className="space-y-6">
    <section className={`rounded-premium border p-5 flex items-center justify-between ${semantic.active ? 'bg-success/5 border-success/20' : 'bg-warning/5 border-warning/20'}`}><div className="flex items-center space-x-3"><span className={`material-symbols-outlined ${semantic.active ? 'text-success' : 'text-warning'}`}>hub</span><div><p className="text-sm font-bold text-slate-900">Hybrid semantic retrieval {semantic.active ? 'active' : 'not active for this run'}</p><p className="text-xs text-slate-500 mt-1">{semantic.status?.model || 'MiniLM'} · {(semantic.status?.candidate_count || 0).toLocaleString()} offline candidate vectors · no network during ranking</p></div></div><span className="text-xs font-mono text-slate-400">explicit evidence + cosine retrieval</span></section>
    <div className="grid grid-cols-4 gap-6">
      <Kpi label="Average match" value={`${data?.average_score || 0}%`} note="Final top-100 fit" icon="target" tone="text-primary bg-primary/10" />
      <Kpi label="Availability" value={`${data?.average_availability_score || 0}%`} note={`${data?.open_to_work_rate || 0}% open to work`} icon="event_available" tone="text-success bg-success/10" />
      <Kpi label="Recruiter response" value={`${data?.average_response_rate || 0}%`} note={`${data?.average_interview_show_rate || 0}% interview show rate`} icon="forum" tone="text-accent bg-accent/10" />
      <Kpi label="Average notice" value={`${data?.average_notice_period_days || 0}d`} note="Soft penalty, not a hard filter" icon="schedule" tone="text-warning bg-warning/10" />
    </div>

    <Instruction title="Quality decision instructions" steps={[
      'Career fit and skill depth carry the most weight; listed keywords alone are insufficient.',
      'Exact means structured skill evidence; semantic means corroborating career/profile evidence.',
      'Missing behavioral values such as offer history are treated as neutral, never as zero.',
      'Notice period and location are soft constraints so exceptional candidates remain discoverable.',
      'Use integrity evidence and reasoning QA together before approving a shortlist.',
    ]} />

    <div className="grid grid-cols-2 gap-6">
      <ChartCard title="Average score components" subtitle="Average contribution and maximum available points.">
        <ResponsiveContainer width="100%" height="100%"><BarChart data={data?.component_averages || []} layout="vertical" margin={{ left: 45 }}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" domain={[0, 40]} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" axisLine={false} tickLine={false} width={130} fontSize={11}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="value" fill="#2563EB" radius={[0, 8, 8, 0]} barSize={20}/></BarChart></ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Experience-band fit" subtitle="Alignment with the JD's 5-9 year target.">
        <Donut data={data?.experience_distribution || []} />
      </ChartCard>
    </div>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100">
      <h3 className="font-bold text-slate-900 text-lg">Required-skill evidence coverage</h3><p className="text-sm text-slate-500 mb-6">Exact, semantic, and missing evidence across the ranked 100.</p>
      <div className="space-y-5">{(data?.requirement_coverage || []).map((item) => <div key={item.name}><div className="flex justify-between text-sm mb-2"><span className="font-bold text-slate-700">{item.name}</span><span className="font-bold text-primary">{item.coverage}% covered</span></div><div className="h-3 bg-slate-100 rounded-full overflow-hidden flex"><span className="bg-success h-full" style={{ width: `${item.exact}%` }}/><span className="bg-primary h-full" style={{ width: `${item.semantic}%` }}/><span className="bg-danger h-full" style={{ width: `${item.missing}%` }}/></div><div className="flex space-x-4 mt-1.5 text-[10px] text-slate-400"><span>Exact {item.exact}</span><span>Semantic {item.semantic}</span><span>Missing {item.missing}</span></div></div>)}</div>
    </section>

    <div className="grid grid-cols-3 gap-6">
      <ChartCard title="Notice-period risk" subtitle="Availability constraint distribution."><Donut data={data?.notice_distribution || []} /></ChartCard>
      <ChartCard title="Integrity failure reasons" subtitle="All reasons recorded for excluded profiles."><ResponsiveContainer width="100%" height="100%"><BarChart data={data?.integrity_reason_distribution || []} layout="vertical" margin={{ left: 60 }}><XAxis type="number" axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" axisLine={false} tickLine={false} width={150} fontSize={10}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="value" fill="#EF4444" radius={[0,8,8,0]} barSize={18}/></BarChart></ResponsiveContainer></ChartCard>
      <ChartCard title="Company background" subtitle="Product/non-services versus services-only."><Donut data={data?.company_background || []} /></ChartCard>
    </div>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100">
      <div className="flex justify-between items-start mb-5"><div><h3 className="font-bold text-slate-900 text-lg">Reasoning quality audit</h3><p className="text-sm text-slate-500">The official Stage 4 review samples ten random reasoning strings.</p></div><span className="text-xs font-mono text-primary bg-primary/10 px-3 py-2 rounded-xl">{reasoning.source}</span></div>
      <div className="grid grid-cols-3 gap-4"><SmallMetric label="Non-empty" value={`${reasoning.non_empty_rate || 0}%`} /><SmallMetric label="Unique strings" value={`${reasoning.unique_rate || 0}%`} /><SmallMetric label="Concern coverage" value={`${reasoning.concern_coverage_rate || 0}%`} /></div>
    </section>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900 text-lg">All 23 Redrob behavioral signals</h3><p className="text-sm text-slate-500 mb-5">Grouped exactly by the recruiter decision each signal supports.</p><div className="grid grid-cols-5 gap-4">{(data?.challenge?.behavioral_signal_groups || []).map((group) => <div key={group.name} className="bg-slate-50 border border-slate-100 rounded-2xl p-4"><p className="text-xs font-bold text-slate-800 mb-3">{group.name}</p><div className="space-y-2">{group.signals.map((signal) => <p key={signal} className="text-[10px] font-mono text-slate-500 break-words">{signal}</p>)}</div></div>)}</div></section>
  </div>
}

function Cost({ data }) {
  return <div className="space-y-6">
    <div className="grid grid-cols-5 gap-5">
      <Kpi label="Top-10 CPH" value={inr(data?.average_top10_cph_inr, true)} note="Priority calling portfolio" icon="payments" tone="text-success bg-success/10" />
      <Kpi label="Top-100 CPH" value={inr(data?.average_shortlist_cph_inr, true)} note="Entire shortlist average" icon="account_balance_wallet" tone="text-primary bg-primary/10" />
      <Kpi label="Benchmark" value={inr(data?.cph_benchmark_inr, true)} note="Comparison baseline" icon="balance" tone="text-slate-600 bg-slate-100" />
      <Kpi label="Top-10 savings" value={inr(data?.top10_savings_inr, true)} note="Projected portfolio impact" icon="savings" tone="text-accent bg-accent/10" />
      <Kpi label="Salary overlap" value={`${data?.salary_overlap_rate || 0}%`} note="Expected range intersects budget" icon="handshake" tone="text-warning bg-warning/10" />
    </div>

    <Instruction title="How to use cost analytics" steps={[
      'CPH is a decision forecast, not an accounting ledger or guaranteed spend.',
      'It combines recruiter touchpoints, vacancy delay, interview/offer drop-off, and salary mismatch.',
      'Compare candidates only after minimum fit and integrity thresholds are satisfied.',
      'Use top-10 portfolio savings for prioritization; do not reject a rare high-fit candidate solely on CPH.',
      'Calibrate benchmark and vacancy-day cost with the employer before production use.',
    ]} />

    <div className="grid grid-cols-2 gap-6">
      <ChartCard title="Projected CPH distribution" subtitle="Cost-to-hire bands across the shortlist."><Donut data={data?.cph_distribution || []} /></ChartCard>
      <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900 text-lg">CPH model inputs</h3><p className="text-sm text-slate-500 mb-6">Candidate-level values are visible in every evidence drawer.</p><div className="space-y-4">{[
        ['Recruiter coordination', 'Expected touchpoints derived from recruiter response rate'],
        ['Vacancy delay', 'Notice period plus a bounded onboarding buffer'],
        ['Drop-off risk', 'Interview completion and known/neutral offer acceptance'],
        ['Salary mismatch', 'Expected minimum above the job budget'],
      ].map(([name, description], index) => <div key={name} className="flex space-x-3"><span className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">{index + 1}</span><div><p className="text-sm font-bold text-slate-800">{name}</p><p className="text-xs text-slate-500 mt-1">{description}</p></div></div>)}</div></section>
    </div>
  </div>
}

function Readiness({ data }) {
  const readiness = data?.submission_readiness || {}
  const challenge = data?.challenge || {}
  return <div className="space-y-6">
    <div className="flex justify-end space-x-3"><a href={apiUrl('/review/top50.csv')} className="text-xs font-bold text-primary bg-primary/10 px-4 py-2.5 rounded-xl">Download human top-50 sheet</a><a href={apiUrl('/review/reasoning-sample.csv')} className="text-xs font-bold text-accent bg-accent/10 px-4 py-2.5 rounded-xl">Download blind reasoning sample</a></div>
    <section className="grid grid-cols-3 gap-6">
      <div className="col-span-2 bg-slate-900 text-white rounded-premium p-7"><p className="text-xs text-blue-300 uppercase tracking-widest font-bold">What Redrob actually wants</p><h2 className="text-2xl font-bold mt-2">{challenge.deliverable}</h2><p className="text-sm text-slate-300 mt-3">The web app differentiates the project, but the validated ranking CSV and hidden-ground-truth quality decide whether the team advances.</p></div>
      <div className="bg-white rounded-premium shadow-premium border border-slate-100 p-6"><div className="flex justify-between"><div><p className="text-xs uppercase tracking-wider font-bold text-slate-400">Automated readiness</p><p className="text-4xl font-bold text-success mt-2">{readiness.automated_score || 0}%</p></div><span className="material-symbols-outlined text-success text-4xl">verified</span></div><p className="text-xs text-slate-500 mt-3">Handoff readiness: {readiness.handoff_score || 0}% · portal ready: {readiness.portal_ready ? 'yes' : 'no'}</p></div>
    </section>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900 text-lg">Automated submission checks</h3><p className="text-sm text-slate-500 mb-5">Derived from the latest persisted full ranking.</p><div className="grid grid-cols-2 gap-3">{(readiness.automated_checks || []).map((check) => <Check key={check.name} item={{ ...check, status: check.passed ? 'ready' : 'action' }} />)}</div></section>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900 text-lg">Required handoff actions</h3><p className="text-sm text-slate-500 mb-5">These cannot be inferred from ranking quality and must be completed before upload.</p><div className="grid grid-cols-2 gap-3">{(readiness.handoff_items || []).map((item) => <Check key={item.name} item={item} />)}</div></section>

    <div className="grid grid-cols-4 gap-5">{(challenge.scoring_metrics || []).map((metric) => <div key={metric.name} className="bg-white p-5 rounded-premium shadow-premium border border-slate-100"><div className="flex justify-between items-start"><p className="font-bold text-slate-900">{metric.name}</p><span className="text-xl font-bold text-primary">{metric.weight}%</span></div><p className="text-xs text-slate-500 leading-relaxed mt-3">{metric.purpose}</p></div>)}</div>

    <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900 text-lg">Official five-stage evaluation pipeline</h3><div className="space-y-4 mt-5">{(challenge.evaluation_stages || []).map((stage) => <div key={stage.stage} className="grid grid-cols-[48px_1fr_1fr] gap-4 items-start border border-slate-100 rounded-2xl p-4"><span className="w-10 h-10 bg-primary/10 text-primary rounded-xl flex items-center justify-center font-bold">{stage.stage}</span><div><p className="text-sm font-bold text-slate-900">{stage.name}</p><p className="text-xs text-slate-500 mt-1">{stage.checks}</p></div><div className="bg-danger/5 text-danger rounded-xl p-3 text-xs"><strong>Elimination:</strong> {stage.elimination}</div></div>)}</div></section>

    <div className="grid grid-cols-2 gap-6"><section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900">Reasoning review checklist</h3><ul className="space-y-3 mt-5">{(challenge.reasoning_checks || []).map((item) => <li key={item} className="flex items-start space-x-2 text-sm text-slate-600"><span className="material-symbols-outlined text-success text-[18px]">check_circle</span><span>{item}</span></li>)}</ul></section><section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><h3 className="font-bold text-slate-900">Submission instructions</h3><ol className="space-y-3 mt-5">{(challenge.submission_requirements || []).map((item, index) => <li key={item} className="flex items-start space-x-3 text-sm text-slate-600"><span className="text-xs font-bold text-primary bg-primary/10 w-6 h-6 rounded-lg flex items-center justify-center shrink-0">{index + 1}</span><span>{item}</span></li>)}</ol></section></div>

    <Instruction title="Winning priorities from this point" steps={[
      'Manually review the top 10 and top 50 against the full profiles; hidden NDCG quality dominates the score.',
      'Create authentic iterative Git commits and make every team member able to defend the weights and integrity rules.',
      'Add the required root submission metadata and a working hosted sample sandbox or public Docker recipe.',
      'Run a blind audit of ten random reasoning rows for specificity, honesty, variation, and rank consistency.',
      'Do not spend time adding infrastructure that does not improve ranking quality, reproducibility, or the judge demo.',
    ]} />
  </div>
}

function ProductActivity({ data = {} }) {
  return <section className="bg-white p-7 rounded-premium shadow-premium border border-slate-100"><div className="flex justify-between items-start"><div><h3 className="font-bold text-slate-900 text-lg">Local product activity</h3><p className="text-sm text-slate-500">Privacy-preserving SaaS events stored in SQLite; no external analytics dependency.</p></div><span className="text-xs font-mono text-slate-400">past events</span></div><div className="grid grid-cols-6 gap-3 mt-5">{(data.counts || []).map((event) => <div key={event.event_name} className="bg-slate-50 border border-slate-100 rounded-2xl p-3"><p className="text-[10px] font-mono text-slate-500 break-words">{event.event_name}</p><p className="text-xl font-bold text-slate-900 mt-2">{event.count}</p></div>)}</div></section>
}

function Check({ item }) {
  const ready = item.status === 'ready'
  return <div className={`border rounded-2xl p-4 flex items-start space-x-3 ${ready ? 'border-success/20 bg-success/5' : 'border-warning/20 bg-warning/5'}`}><span className={`material-symbols-outlined text-[20px] ${ready ? 'text-success' : 'text-warning'}`}>{ready ? 'check_circle' : 'pending_actions'}</span><div><p className="text-sm font-bold text-slate-800">{item.name}</p><p className="text-xs text-slate-500 mt-1 leading-relaxed">{item.detail}</p></div></div>
}

function Instruction({ title, steps }) {
  return <section className="bg-primary/5 border border-primary/10 rounded-premium p-6"><div className="flex items-center space-x-2 mb-4"><span className="material-symbols-outlined text-primary">menu_book</span><h3 className="font-bold text-slate-900">{title}</h3></div><ol className="grid grid-cols-5 gap-4">{steps.map((step, index) => <li key={step} className="text-xs text-slate-600 leading-relaxed"><span className="block text-primary font-bold mb-1">0{index + 1}</span>{step}</li>)}</ol></section>
}

function ChartCard({ title, subtitle, children, className = '' }) {
  return <section className={`bg-white p-6 rounded-premium shadow-premium border border-slate-100 ${className}`}><h3 className="font-bold text-slate-900 text-lg">{title}</h3><p className="text-sm text-slate-500 mb-5">{subtitle}</p><div className="h-[280px]">{children}</div></section>
}

function Donut({ data }) {
  return <div className="h-full flex items-center"><div className="h-full flex-1"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} innerRadius={58} outerRadius={85} paddingAngle={4} dataKey="value" stroke="none">{data.map((entry, index) => <Cell key={entry.name} fill={COLORS[index % COLORS.length]}/>)}</Pie><Tooltip contentStyle={tooltipStyle}/></PieChart></ResponsiveContainer></div><div className="w-40 space-y-2">{data.map((entry, index) => <div key={entry.name} className="flex justify-between text-[11px]"><span className="flex items-center text-slate-500"><i className="w-2 h-2 rounded-full mr-1.5" style={{ background: COLORS[index % COLORS.length] }}/>{entry.name}</span><strong className="text-slate-800 ml-2">{entry.value}</strong></div>)}</div></div>
}

function Kpi({ label, value, note, icon, tone }) {
  const [text, bg] = tone.split(' ')
  return <div className="bg-white p-5 rounded-premium shadow-premium border border-slate-100"><div className={`w-10 h-10 rounded-2xl ${bg} ${text} flex items-center justify-center mb-4`}><span className="material-symbols-outlined text-[21px]">{icon}</span></div><p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">{label}</p><h3 className="text-2xl font-bold text-slate-900 mt-1">{value}</h3><p className="text-xs text-slate-500 mt-2">{note}</p></div>
}

function SmallMetric({ label, value }) {
  return <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4"><p className="text-xs text-slate-500">{label}</p><p className="text-xl font-bold text-slate-900 mt-1">{value}</p></div>
}

const tooltipStyle = { borderRadius: 12, border: 'none', boxShadow: '0 10px 30px rgba(15,23,42,0.1)' }
