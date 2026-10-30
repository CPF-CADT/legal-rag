import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, SourceCard, StatePanel } from '../components/common/UI'
import { apiClient } from '../services/api'
import type { ChatMessageInput, ChatResponse } from '../types'

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageInput[]>([])
  const [input, setInput] = useState('')
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastQuestion, setLastQuestion] = useState('')

  const send = async (event?: FormEvent, question = input.trim(), appendUser = true) => {
    event?.preventDefault()
    if (!question || loading) return
    if (appendUser) setMessages((items) => [...items, { role: 'user', content: question }])
    setLastQuestion(question)
    setInput('')
    setError('')
    setLoading(true)
    try {
      const next = await apiClient.chat(question, messages)
      setResponse(next)
      const assistantMessage = next.answer ?? next.insufficientEvidenceMessage ?? 'មិនអាចរកឃើញចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់ទេ។'
      setMessages((items) => [...items, { role: 'assistant', content: assistantMessage }])
    } catch {
      setError('ការស្នើសុំបរាជ័យ។ សូមព្យាយាមម្តងទៀត។')
    } finally {
      setLoading(false)
    }
  }

  const clear = () => {
    setMessages([])
    setResponse(null)
    setError('')
    setLastQuestion('')
  }

  return <section className="mx-auto flex min-h-[calc(100vh-9rem)] w-full max-w-5xl flex-col bg-white p-4 sm:p-6 lg:p-8">
    <div className="flex items-center justify-between gap-4 pb-5">
      <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 text-sm font-black text-white">ធី</div><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">LegalRAG · Thita</p><h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">សួរសំណួរអំពីច្បាប់</h1></div></div>
      <div className="flex items-center gap-2"><Link to="/search" className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">ស្វែងរកច្បាប់</Link><button type="button" onClick={clear} className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100">សម្អាត</button></div>
    </div>
    <div className="chat-scrollbar flex-1 space-y-5 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 sm:border-0 sm:p-8">
      {messages.length === 0 && <div className="flex min-h-[420px] items-center justify-center text-center"><div className="max-w-xl"><div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-slate-100 text-2xl font-black text-blue-600">ធី</div><p className="mt-6 text-sm font-bold uppercase tracking-[0.18em] text-slate-500">សួស្តី! ខ្ញុំគឺធីតា</p><h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl">តើអ្នកចង់ស្វែងយល់អ្វី?</h2><p className="mt-4 text-base leading-8 text-slate-600">សួរអំពីមាត្រា ឬលក្ខខណ្ឌក្នុងច្បាប់កម្ពុជា។ ខ្ញុំនឹងបង្ហាញចម្លើយជាមួយប្រភព PDF ដើម។</p><div className="mt-7 flex flex-wrap justify-center gap-2 text-sm text-slate-600"><button type="button" onClick={() => setInput('តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?')} className="rounded-full border border-slate-200 bg-white px-4 py-2.5 transition hover:border-slate-400 hover:bg-slate-50">តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?</button><button type="button" onClick={() => setInput('ស្វែងរកមាត្រា ៨')} className="rounded-full border border-slate-200 bg-white px-4 py-2.5 transition hover:border-slate-400 hover:bg-slate-50">ស្វែងរកមាត្រា ៨</button></div></div></div>}
      {messages.map((message, index) => message.role === 'assistant' ? <div key={`${message.role}-${index}`} className="flex items-start gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold text-blue-600">ធី</div><div className="max-w-[90%]"><p className="mb-1 text-xs font-semibold text-slate-500">ធីតា</p><div className="khmer-text whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white px-4 py-3 leading-7 text-slate-800">{message.content}</div></div></div> : <div key={`${message.role}-${index}`} className="flex justify-end"><div className="max-w-[90%]"><p className="mb-1 text-right text-xs font-semibold text-slate-500">អ្នក</p><div className="khmer-text whitespace-pre-wrap rounded-2xl bg-slate-100 px-4 py-3 leading-7 text-slate-800">{message.content}</div></div></div>)}
      {loading && <div className="flex items-start gap-3" aria-label="ធីតាកំពុងវាយ…"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold text-blue-600">ធី</div><div><p className="mb-1 text-xs font-semibold text-slate-500">ធីតា កំពុងវាយ…</p><div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white px-4 py-3"><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" /></div></div></div>}
      {error && <div className="space-y-3"><StatePanel title={error} tone="error" /><Button variant="secondary" onClick={() => void send(undefined, lastQuestion, false)}>ព្យាយាមម្តងទៀត</Button></div>}
      {response && !response.hasSufficientEvidence && <StatePanel title="មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់" description={response.insufficientEvidenceMessage ?? undefined} tone="warning" />}
      {response?.hasSufficientEvidence && response.sources.length > 0 && <div className="space-y-3 pt-2"><h2 className="text-lg font-bold">ប្រភពយោង</h2>{response.sources.map((source) => <SourceCard key={`${source.documentId}-${source.articleNumber}`} source={source} compact />)}</div>}
    </div>
    <form onSubmit={(event) => void send(event)} className="mt-4 flex gap-3 rounded-2xl border border-slate-300 bg-white p-3 shadow-sm"><textarea value={input} onChange={(event) => setInput(event.target.value)} rows={2} className="flex-1 resize-none rounded-xl border-0 bg-transparent px-4 py-3 outline-none ring-0 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-200" placeholder="សួរសំណួររបស់អ្នក…" aria-label="សំណួររបស់អ្នក" /><Button type="submit" disabled={loading || !input.trim()}>ផ្ញើ ↗</Button></form>
    <p className="pt-3 text-center text-xs text-slate-400">ធីតាផ្តល់ព័ត៌មានសម្រាប់ជំនួយប៉ុណ្ណោះ។ សូមពិនិត្យប្រភព PDF ដើម។</p>
  </section>
}
