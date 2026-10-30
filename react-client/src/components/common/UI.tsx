import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Citation, SearchMode } from '../../types'

export function Button({ children, type = 'button', variant = 'primary', disabled, onClick }: { children: ReactNode; type?: 'button' | 'submit'; variant?: 'primary' | 'secondary' | 'ghost'; disabled?: boolean; onClick?: () => void }) {
  const styles = { primary: 'bg-blue-700 text-white hover:bg-blue-800', secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50', ghost: 'text-slate-600 hover:bg-slate-100' }
  return <button type={type} disabled={disabled} onClick={onClick} className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]}`}>{children}</button>
}

export function ModeSelector({ value, onChange }: { value: SearchMode; onChange: (mode: SearchMode) => void }) {
  const modes: { value: SearchMode; label: string }[] = [
    { value: 'keyword', label: 'ពាក្យគន្លឹះ' },
    { value: 'semantic', label: 'ស្វែងរកន័យ' },
    { value: 'exact_article', label: 'មាត្រាជាក់លាក់' },
  ]
  return <div className="flex flex-wrap gap-2" aria-label="Search mode">{modes.map((mode) => <button key={mode.value} type="button" onClick={() => onChange(mode.value)} className={`rounded-full border px-3 py-1.5 text-sm ${value === mode.value ? 'border-blue-700 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:border-blue-300'}`}>{mode.label}</button>)}</div>
}

export function StatePanel({ title, description, tone = 'neutral' }: { title: string; description?: string; tone?: 'neutral' | 'error' | 'warning' }) {
  const colors = tone === 'error' ? 'border-red-200 bg-red-50 text-red-900' : tone === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-slate-200 bg-white text-slate-700'
  return <div className={`rounded-xl border p-8 text-center ${colors}`} role="status"><p className="font-semibold">{title}</p>{description && <p className="mt-2 text-sm opacity-80">{description}</p>}</div>
}

export function LoadingPanel() { return <StatePanel title="កំពុងស្វែងរក…" description="សូមរង់ចាំបន្តិច។" /> }

export function PdfLink({ url, label = 'បើក PDF ដើម' }: { url: string | null; label?: string }) {
  if (!url) return <span className="text-sm text-slate-400">មិនមានតំណ PDF</span>
  return <a href={url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-blue-700 hover:text-blue-900">↗ {label}</a>
}

export function SourceCard({ source }: { source: Citation }) {
  return <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">ប្រភពយោង</p><h3 className="mt-1 font-semibold text-slate-900">{source.title}</h3></div>
      {source.score != null && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">ភាពពាក់ព័ន្ធ {Math.round(source.score * 100)}%</span>}
    </div>
    <p className="mt-3 text-sm text-slate-600">មាត្រា {source.articleNumber ?? '—'}{source.chapterTitle ? ` · ${source.chapterTitle}` : ''}{source.sectionTitle ? ` · ${source.sectionTitle}` : ''}</p>
    {source.excerpt && <p className="khmer-text mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{source.excerpt}</p>}
    <div className="mt-4 flex flex-wrap gap-4"><Link to={`/articles/${source.documentId}/${encodeURIComponent(source.articleNumber ?? '')}`} className="text-sm font-semibold text-blue-700 hover:text-blue-900">អានអត្ថបទ →</Link><PdfLink url={source.pdfUrl} /></div>
  </article>
}
