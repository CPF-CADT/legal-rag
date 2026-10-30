import { FormEvent, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button, LoadingPanel, ModeSelector, SourceCard, StatePanel } from '../components/common/UI'
import { apiClient } from '../services/api'
import type { SearchFilters, SearchMode, SearchResponse } from '../types'

export function SearchResultsPage() {
  const [params, setParams] = useSearchParams()
  const initialQuery = params.get('q') ?? ''
  const [query, setQuery] = useState(initialQuery)
  const [mode, setMode] = useState<SearchMode>((params.get('mode') as SearchMode) || 'semantic')
  const [documentTitle, setDocumentTitle] = useState(params.get('title') ?? '')
  const [documentType, setDocumentType] = useState(params.get('type') ?? '')
  const [category, setCategory] = useState(params.get('category') ?? '')
  const [chapterNumber, setChapterNumber] = useState(params.get('chapter') ?? '')
  const [articleNumber, setArticleNumber] = useState(params.get('article') ?? '')
  const [page, setPage] = useState(Number(params.get('page') ?? 1))
  const [pageSize, setPageSize] = useState(Number(params.get('pageSize') ?? 10))
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runSearch = async (event?: FormEvent, requestedPage = 1, requestedPageSize = pageSize) => {
    event?.preventDefault()
    if (!query.trim() && mode !== 'exact_article' && !articleNumber.trim()) return
    setLoading(true); setError('')
    const filters: SearchFilters = { documentTitle: documentTitle.trim() || null, documentType: documentType || null, category: category || null, chapterNumber: chapterNumber.trim() || null, articleNumber: articleNumber.trim() || (mode === 'exact_article' ? query.trim() : null) }
    setPage(requestedPage); setPageSize(requestedPageSize)
    setParams({ q: query, mode, page: String(requestedPage), pageSize: String(requestedPageSize), ...(documentTitle && { title: documentTitle }), ...(documentType && { type: documentType }), ...(category && { category }), ...(chapterNumber && { chapter: chapterNumber }), ...(articleNumber && { article: articleNumber }) })
    try { setResult(await apiClient.search({ query, mode, filters, page: requestedPage, pageSize: requestedPageSize })) } catch { setError('មិនអាចស្វែងរកបានទេ។ សូមព្យាយាមម្តងទៀត។') } finally { setLoading(false) }
  }

  useEffect(() => { if (initialQuery || params.get('article')) void runSearch(undefined, page, pageSize) }, [])

  return <section className="space-y-6">
    <form onSubmit={runSearch} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="flex flex-col gap-3 sm:flex-row"><input value={query} onChange={(event) => setQuery(event.target.value)} className="min-h-11 flex-1 rounded-lg border border-slate-200 px-4 outline-none focus:ring-2 focus:ring-blue-500" placeholder="ស្វែងរកច្បាប់…" /><Button type="submit" disabled={loading}>ស្វែងរក</Button></div><div className="mt-3"><ModeSelector value={mode} onChange={setMode} /></div></form>
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]"><aside className="h-fit rounded-xl border border-slate-200 bg-white p-5"><p className="font-semibold">តម្រងស្វែងរក</p><label className="mt-5 block text-sm text-slate-600">ចំណងជើងឯកសារ<input value={documentTitle} onChange={(event) => setDocumentTitle(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2" placeholder="ស្វែងរកតាមចំណងជើង" /></label><label className="mt-4 block text-sm text-slate-600">ប្រភេទឯកសារ<select value={documentType} onChange={(event) => setDocumentType(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2"><option value="">គ្រប់ប្រភេទ</option><option value="Law">ច្បាប់</option></select></label><label className="mt-4 block text-sm text-slate-600">ប្រភេទច្បាប់<select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2"><option value="">គ្រប់ប្រភេទ</option><option value="ចរាចរណ៍">ចរាចរណ៍</option></select></label><label className="mt-4 block text-sm text-slate-600">លេខជំពូក<input value={chapterNumber} onChange={(event) => setChapterNumber(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2" placeholder="ឧ. ១" /></label><label className="mt-4 block text-sm text-slate-600">លេខមាត្រា<input value={articleNumber} onChange={(event) => setArticleNumber(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2" placeholder="ឧ. ៨" /></label><p className="mt-5 text-xs leading-6 text-slate-500">តម្រងទាំងនេះត្រូវបានផ្ញើទៅ API ជាមួយសំណួរ។</p></aside>
      <div className="space-y-4"><div className="flex items-end justify-between"><div><p className="text-sm text-slate-500">លទ្ធផលស្វែងរក</p><h1 className="text-2xl font-bold">{query || articleNumber ? query || `មាត្រា ${articleNumber}` : 'បញ្ចូលសំណួរដើម្បីស្វែងរក'}</h1></div>{result && <span className="text-sm text-slate-500">{result.pagination.total} លទ្ធផល</span>}</div>{error && <StatePanel title={error} tone="error" />}{loading && <LoadingPanel />}{!loading && !error && result && !result.hasSufficientEvidence && <StatePanel title="រកមិនឃើញលទ្ធផល" description="សូមសាកល្បងពាក្យគន្លឹះ ឬតម្រងផ្សេងទៀត។" />}{!loading && !error && result?.items.map((item) => <SourceCard key={`${item.documentId}-${item.articleNumber}`} source={item} />)}{!loading && !error && !result && <StatePanel title="ចាប់ផ្តើមស្វែងរក" description="ស្វែងរកតាមពាក្យគន្លឹះ ឬសួរសំណួរជាភាសាខ្មែរ។" />}{result && result.pagination.totalPages > 1 && <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3"><Button variant="secondary" disabled={loading || page <= 1} onClick={() => void runSearch(undefined, page - 1)}>← មុន</Button><span className="text-sm text-slate-600">ទំព័រ {page} / {result.pagination.totalPages}</span><Button variant="secondary" disabled={loading || page >= result.pagination.totalPages} onClick={() => void runSearch(undefined, page + 1)}>បន្ទាប់ →</Button><label className="text-sm text-slate-600">ក្នុងមួយទំព័រ<select value={pageSize} onChange={(event) => void runSearch(undefined, 1, Number(event.target.value))} className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1"><option value="10">10</option><option value="20">20</option><option value="50">50</option></select></label></div>}</div></div><p className="text-sm text-slate-500"><Link to="/chat" className="font-semibold text-blue-700">ចង់សួរជាសន្ទនា? បើក Chat →</Link></p>
  </section>
}
