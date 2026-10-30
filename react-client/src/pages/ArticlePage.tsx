import { Link, useNavigate, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Button, LoadingPanel, PdfLink, StatePanel } from '../components/common/UI'
import { apiClient } from '../services/api'
import type { ArticleResponse } from '../types'

export function ArticlePage() {
  const { documentId, articleNumber } = useParams(); const navigate = useNavigate(); const [data, setData] = useState<ArticleResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  const load = () => { if (!documentId || !articleNumber) return; setLoading(true); setError(''); void apiClient.getArticle(documentId, decodeURIComponent(articleNumber)).then(setData).catch(() => setError('មិនអាចទាញយកអត្ថបទបានទេ។ សូមព្យាយាមម្តងទៀត។')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [documentId, articleNumber])
  if (loading) return <LoadingPanel />
  if (error) return <div className="space-y-4"><StatePanel title={error} tone="error" /><Button variant="secondary" onClick={load}>ព្យាយាមម្តងទៀត</Button></div>
  if (!data) return <div className="space-y-4"><StatePanel title="រកមិនឃើញអត្ថបទ" description="អត្ថបទនេះមិនមាននៅក្នុងទិន្នន័យគំរូទេ។" tone="error" /><Link to="/search" className="inline-block font-semibold text-blue-700 hover:text-blue-900">← ត្រឡប់ទៅស្វែងរក</Link></div>
  const { article, navigation } = data
  return <article className="mx-auto max-w-4xl space-y-6"><div className="flex flex-wrap items-center justify-between gap-3"><Link to="/search" className="text-sm font-semibold text-blue-700">← ត្រឡប់ទៅលទ្ធផល</Link><PdfLink url={article.pdfUrl} label="បើក PDF ដើម" /></div><header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-semibold text-blue-700">{article.documentType} {article.documentNumber ? `· ${article.documentNumber}` : ''}</p><h1 className="mt-2 text-2xl font-bold text-slate-950">{article.title}</h1><p className="mt-4 text-slate-600">{article.chapterTitle ? `ជំពូក ${article.chapterTitle} · ` : ''}{article.sectionTitle ? `ផ្នែក ${article.sectionTitle} · ` : ''}មាត្រា {article.articleNumber}</p></header><section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">អត្ថបទដើម</h2><div className="khmer-text mt-5 whitespace-pre-wrap text-base leading-8 text-slate-900">{article.articleText}</div></section><div className="flex flex-wrap justify-between gap-3"><Button variant="secondary" disabled={!navigation.previousArticleNumber} onClick={() => navigation.previousArticleNumber && navigate(`/articles/${article.documentId}/${navigation.previousArticleNumber}`)}>← មាត្រាមុន</Button><Button variant="secondary" disabled={!navigation.nextArticleNumber} onClick={() => navigation.nextArticleNumber && navigate(`/articles/${article.documentId}/${navigation.nextArticleNumber}`)}>មាត្រាបន្ទាប់ →</Button></div></article>
}
