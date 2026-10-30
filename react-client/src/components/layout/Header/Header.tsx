import { Link, NavLink } from 'react-router-dom'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-slate-100 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="text-xl font-bold tracking-tight text-blue-800">LegalRAG</Link>
        <nav aria-label="Main navigation" className="flex items-center gap-1">
          <NavLink to="/search" className={navClass}>ស្វែងរក</NavLink>
          <NavLink to="/chat" className={navClass}>សួរសំណួរ</NavLink>
        </nav>
      </div>
    </header>
  )
}
