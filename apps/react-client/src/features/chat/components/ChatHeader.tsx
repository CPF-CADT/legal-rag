import { Link } from 'react-router-dom'
import { IconSearch, IconSidebar } from '../../../components/common/Icons'

interface ChatHeaderProps {
  onToggleSidebar: () => void
  onClearSession: () => void
  canClear: boolean
}

export function ChatHeader({
  onToggleSidebar,
  onClearSession,
  canClear,
}: ChatHeaderProps) {
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-slate-200/80 bg-white/95 px-3 sm:px-4 backdrop-blur-md">
      <div className="flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          title="បើក/បិទ ម៉ឺនុយ"
          aria-label="បើក/បិទ ម៉ឺនុយ"
        >
          <IconSidebar className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-900 text-sm sm:text-base">
            ជំនួយការច្បាប់ · ធីតា
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] sm:text-xs font-medium text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>ត្រៀមឆ្លើយ</span>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        <Link
          to="/search"
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <IconSearch className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">ស្វែងរកច្បាប់</span>
        </Link>

        {canClear && (
          <button
            type="button"
            onClick={onClearSession}
            className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            សម្អាត
          </button>
        )}

      </div>
    </header>
  )
}

