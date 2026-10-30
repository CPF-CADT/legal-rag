import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, ModeSelector } from '../components/common/UI'
import type { SearchMode } from '../types'

export function HomePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<SearchMode>('semantic')
  const submit = (event: FormEvent) => { event.preventDefault(); if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}&mode=${mode}`) }
  return (
    <section className="mx-auto max-w-4xl py-10 sm:py-16">
      <div className="text-center"><p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Khmer Legal AI</p><h1 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-5xl">ស្វែងរកច្បាប់ ឬសួរសំណួរអំពីច្បាប់</h1><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-600">ស្វែងរកឯកសារច្បាប់កម្ពុជា ដោយមានប្រភពយោងច្បាស់លាស់ និងតំណ PDF ដើម។</p></div>
      <form onSubmit={submit} className="mt-10 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl shadow-slate-200/50"><div className="flex flex-col gap-3 sm:flex-row"><input value={query} onChange={(event) => setQuery(event.target.value)} className="min-h-12 flex-1 rounded-lg border border-slate-200 px-4 outline-none ring-blue-500 placeholder:text-slate-400 focus:ring-2" placeholder="ស្វែងរកច្បាប់ ឬសួរសំណួរអំពីច្បាប់…" aria-label="សំណួរស្វែងរក" /><Button type="submit">ស្វែងរក</Button></div><div className="mt-3"><ModeSelector value={mode} onChange={setMode} /></div></form>
      <div className="mt-8 grid gap-3 sm:grid-cols-2"><Link to="/search?q=តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?&mode=semantic" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 hover:border-blue-300">តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?</Link><Link to="/search?q=8&mode=exact_article" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 hover:border-blue-300">ស្វែងរកមាត្រា ៨ នៃច្បាប់ចរាចរណ៍</Link></div>
      <div className="mt-10 text-center"><Link to="/chat" className="font-semibold text-blue-700 hover:text-blue-900">ឬ ចាប់ផ្តើមសួរសំណួរជាមួយ LegalRAG →</Link><p className="mt-5 text-sm text-slate-500">ប្រព័ន្ធនេះផ្តល់ព័ត៌មានប៉ុណ្ណោះ មិនមែនជាដំបូន្មានផ្នែកច្បាប់ទេ។</p></div>
    </section>
  )
}
