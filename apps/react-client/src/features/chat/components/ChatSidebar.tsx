import { Link } from 'react-router-dom'
import type { ChatSession } from '../../../types'
import {
  IconClose,
  IconMessageSquare,
  IconPenEdit,
  IconSearch,
  IconSidebar,
  IconTrash,
} from '../../../components/common/Icons'

interface ChatSidebarProps {
  isOpen: boolean
  onClose: () => void
  onToggle: () => void
  sessions: ChatSession[]
  activeSessionId: string
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onDeleteSession: (id: string) => void
}

export function ChatSidebar({
  isOpen,
  onClose,
  onToggle,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}: ChatSidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-xs md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container with ChatGPT-style light neutral palette */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-[#f9f9f9] border-r border-slate-200/80 text-slate-800 transition-all duration-300 ease-in-out md:static ${
          isOpen
            ? 'w-64 sm:w-68 translate-x-0 opacity-100'
            : 'w-0 -translate-x-full md:translate-x-0 opacity-0 overflow-hidden border-none pointer-events-none'
        }`}
      >
        {/* Top Header: Brand & New Chat */}
        <div className="flex flex-col gap-2 p-3 border-b border-slate-200/60">
          <div className="flex items-center justify-between px-1">
            <span className="flex items-center gap-2 text-sm font-bold tracking-tight text-slate-900">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-blue-600 text-xs font-black text-white">
                ច្បាប់
              </span>
              <span>ជំនួយការច្បាប់</span>
            </span>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={onToggle}
                className="hidden md:inline-flex rounded-lg p-1.5 text-slate-500 hover:bg-slate-200/60 hover:text-slate-800 transition-colors"
                title="បិទម៉ឺនុយ"
                aria-label="បិទម៉ឺនុយ"
              >
                <IconSidebar className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="md:hidden rounded-lg p-1.5 text-slate-500 hover:bg-slate-200/60"
                aria-label="បិទម៉ឺនុយ"
              >
                <IconClose className="h-4 w-4" />
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              onNewSession()
              if (window.innerWidth < 768) onClose()
            }}
            className="mt-1 flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs sm:text-sm font-medium text-slate-800 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-xs"
          >
            <span className="flex items-center gap-2">
              <IconPenEdit className="h-4 w-4 text-blue-600" />
              <span>កិច្ចសន្ទនាថ្មី</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400">⌘K</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5 chat-scrollbar">
          <p className="px-2.5 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            កិច្ចសន្ទនាថ្មីៗ
          </p>

          {sessions.map((session) => {
            const isActive = session.id === activeSessionId
            return (
              <div
                key={session.id}
                className={`group relative flex items-center justify-between rounded-xl px-2.5 py-2 text-xs sm:text-sm transition-all ${
                  isActive
                    ? 'bg-white text-slate-900 font-medium shadow-xs border border-slate-200/80'
                    : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900'
                }`}
              >
                <button
                  type="button"
                  onClick={() => {
                    onSelectSession(session.id)
                    if (window.innerWidth < 768) onClose()
                  }}
                  className="flex min-w-0 flex-1 items-center gap-2 text-left"
                >
                  <IconMessageSquare
                    className={`h-3.5 w-3.5 shrink-0 ${isActive ? 'text-blue-600' : 'text-slate-400'}`}
                  />
                  <span className="truncate">{session.title || 'កិច្ចសន្ទនាគ្មានចំណងជើង'}</span>
                </button>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                  className="ml-1 rounded p-1 text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-slate-100 hover:text-red-600 transition-opacity"
                  title="លុបកិច្ចសន្ទនា"
                  aria-label="លុបកិច្ចសន្ទនា"
                >
                  <IconTrash className="h-3 w-3" />
                </button>
              </div>
            )
          })}
        </div>

        {/* Bottom Section: Search */}
        <div className="p-2.5 border-t border-slate-200/70 space-y-1 bg-[#f9f9f9]">
          <Link
            to="/search"
            className="flex items-center gap-2.5 rounded-xl px-2.5 py-2 text-xs sm:text-sm font-medium text-slate-700 hover:bg-slate-200/50 hover:text-slate-900 transition-colors"
          >
            <IconSearch className="h-4 w-4 text-slate-500" />
            <span>ស្វែងរកមាត្រាច្បាប់</span>
          </Link>

        </div>
      </aside>
    </>
  )
}
