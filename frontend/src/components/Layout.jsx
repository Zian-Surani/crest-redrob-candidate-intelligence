import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useApi } from '../hooks/useApi'
import { initials } from '../lib/api'

export default function Layout() {
  const { data: user } = useApi('/auth/me', { first_name: 'Zian', company: 'CREST Demo' })
  const [search, setSearch] = useState('')

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-body overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col p-10 ml-[328px] max-w-[1400px]">
        <header className="h-16 flex items-center justify-between mb-10">
          <div className="flex flex-col">
            <h1 className="font-headline font-bold text-2xl tracking-tight text-slate-900 flex items-center">
              Good Morning, {user?.first_name || 'Zian'} <span className="ml-2">👋</span>
            </h1>
            <p className="text-slate-500 text-sm mt-1">Hiring Intelligence Dashboard</p>
          </div>
          <div className="flex items-center space-x-4">
            <form
              onSubmit={(event) => {
                event.preventDefault()
                if (search.trim()) window.location.href = `/dashboard/candidates?q=${encodeURIComponent(search)}`
              }}
              className="bg-white border border-slate-200/60 shadow-sm rounded-full px-4 py-2 flex items-center space-x-2 text-sm text-slate-400 w-64 hover:border-primary/30 transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">search</span>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search candidates..." className="bg-transparent outline-none w-full text-slate-700 placeholder:text-slate-400" />
            </form>
            <Link to="/dashboard/jobs" title="Create job" className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5">
              <span className="material-symbols-outlined text-[20px]">add</span>
            </Link>
            <Link to="/dashboard/flagged" title="Integrity alerts" className="relative w-10 h-10 rounded-full bg-white border border-slate-200/60 shadow-sm flex items-center justify-center text-slate-500 hover:text-slate-900 transition-colors">
              <span className="material-symbols-outlined text-[20px]">notifications</span>
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
            </Link>
            <Link to="/dashboard/settings" className="h-10 pl-4 pr-1 py-1 rounded-full bg-white border border-slate-200/60 shadow-sm flex items-center space-x-3 hover:border-slate-300 transition-colors">
              <div className="flex items-center space-x-1">
                <span className="text-[13px] font-semibold text-slate-700">{user?.company || 'CREST Demo'}</span>
                <span className="material-symbols-outlined text-[16px] text-slate-400">expand_more</span>
              </div>
              <div className="w-8 h-8 rounded-full border border-slate-100 bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                {initials(`${user?.first_name || 'Z'} ${user?.last_name || ''}`)}
              </div>
            </Link>
          </div>
        </header>
        <div className="flex-1"><Outlet /></div>
      </main>
    </div>
  )
}
