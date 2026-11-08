import { useState } from 'react'
import type { Citation } from '../../../types'
import { IconBookOpen, IconChevronDown, IconExternalLink } from '../../../components/common/Icons'
import { PdfLink } from '../../../components/common/UI'

interface CitationDrawerProps {
  sources: Citation[]
}

export function CitationDrawer({ sources }: CitationDrawerProps) {
  const [isOpen, setIsOpen] = useState(true)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-4 rounded-xl border border-slate-200/90 bg-slate-50/70 overflow-hidden transition-all text-xs sm:text-sm">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 text-left text-slate-700 hover:bg-slate-100/80 transition-colors"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2 font-medium">
          <IconBookOpen className="h-4 w-4 text-blue-600 shrink-0" />
          <span>ប្រភពយោងផ្លូវការ ({sources.length})</span>
        </span>
        <IconChevronDown
          className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="divide-y divide-slate-200/60 border-t border-slate-200/80 bg-white">
          {sources.map((source, index) => (
            <div key={`${source.documentId}-${source.articleNumber ?? index}`} className="p-3.5 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-semibold text-slate-900">
                  {source.title}{source.articleNumber ? ` · មាត្រា ${source.articleNumber}` : ''}
                </span>
                <div className="flex items-center gap-1 font-medium text-slate-600 hover:text-slate-900">
                  <IconExternalLink className="h-3.5 w-3.5" />
                  <PdfLink url={source.pdfUrl} label="បើកឯកសារដើម" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

