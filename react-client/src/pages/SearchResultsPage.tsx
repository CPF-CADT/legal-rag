import { FormEvent, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button, LoadingPanel, ModeSelector, SourceCard, StatePanel } from '../components/common/UI'
import { searchArticles } from '../services/mockApi'
import type { SearchMode, SearchResponse } from '../types'

export function SearchResultsPage() {
  const [params, setParams] = useSearchParams()
  const initialQuery = params.get('q') ?? ''
  const [query, setQuery] = useState(initialQuery)
  const [mode, setMode] = useState<SearchMode>((params.get('mode') as SearchMode) || 'semantic')
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const runSearch = async (event?: FormEvent) => { event?.preventDefault(); if (!query.trim()) return; setLoading(true); setError(''); setParams({ q: query, mode }); try { setResult(await searchArticles({ query, mode, page: 1, pageSize: 10 })) } catch { setError('មិនអាចស្វែងរកបានទេ។ សូមព្យាយាមម្តងទៀត។') } finally { setLoading(false) } }
  useEffect(() => { if (initialQuery) void runSearch() }, [])
  return <section className="space-y-6"><form onSubmit={runSearch} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="flex flex-col gap-3 sm:flex-row"><input value={query} onChange={(event) => setQuery(event.target.value)} className="min-h-11 flex-1 rounded-lg border border-slate-200 px-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="ស្វែងរកច្បាប់…" /><Button type="submit" disabled={loading}>ស្វែងរក</Button></div><div className="mt-3"><ModeSelector value={mode} onChange={setMode} /></div></form><div className="grid gap-6 lg:grid-cols-[220px_1fr]"><aside className="h-fit rounded-xl border border-slate-200 bg-white p-5"><p className="font-semibold">តម្រងស្វែងរក</p><label className="mt-5 block text-sm text-slate-600">លេខមាត្រា<input className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2" placeholder="ឧ. ៨" /></label><p className="mt-5 text-xs leading-6 text-slate-500">លទ្ធផលស្វែងរកត្រូវបានកំណត់ត្រឹមតែអត្ថបទច្បាប់ មិនរាប់បញ្ចូលបុព្វកថា។</p></aside><div className="space-y-4"><div className="flex items-end justify-between"><div><p className="text-sm text-slate-500">លទ្ធផលស្វែងរក</p><h1 className="text-2xl font-bold">{query || 'បញ្ចូលសំណួរដើម្បីស្វែងរក'}</h1></div>{result && <span className="text-sm text-slate-500">{result.pagination.total} លទ្ធផល</span>}</div>{error && <StatePanel title={error} tone="error" />}{loading && <LoadingPanel />}{!loading && !error && result && !result.hasSufficientEvidence && <StatePanel title="រកមិនឃើញលទ្ធផល" description="សូមសាកល្បងពាក្យគន្លឹះផ្សេងទៀត។" />}{!loading && !error && result?.items.map((item) => <SourceCard key={`${item.documentId}-${item.articleNumber}`} source={item} />)}{!loading && !error && !result && <StatePanel title="ចាប់ផ្តើមស្វែងរក" description="ស្វែងរកតាមពាក្យគន្លឹះ ឬសួរសំណួរជាភាសាខ្មែរ។" />}</div></div><p className="text-sm text-slate-500"><Link to="/chat" className="font-semibold text-blue-700">ចង់សួរជាសន្ទនា? បើក Chat →</Link></p></section>
}
