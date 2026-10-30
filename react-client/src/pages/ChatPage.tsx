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

  return <section className="mx-auto flex min-h-[calc(100vh-9rem)] w-full max-w-4xl flex-col">
    <div className="flex items-center justify-between gap-4 pb-5">
      <div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">LegalRAG Chat</p><h1 className="mt-1 text-2xl font-bold sm:text-3xl">សួរសំណួរអំពីច្បាប់</h1></div>
      <div className="flex items-center gap-2"><Link to="/search" className="rounded-lg px-3 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50">ស្វែងរកច្បាប់</Link><Button variant="ghost" onClick={clear}>សម្អាត</Button></div>
    </div>
    <div className="flex-1 space-y-5 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
      {messages.length === 0 && <div className="flex min-h-[420px] items-center justify-center text-center"><div className="max-w-xl"><div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-blue-700 text-lg font-bold text-white">LR</div><h2 className="mt-6 text-2xl font-bold text-slate-950 sm:text-3xl">តើអ្នកចង់ស្វែងយល់អ្វី?</h2><p className="mt-3 text-slate-600">សួរអំពីមាត្រា ឬលក្ខខណ្ឌដែលមានក្នុងច្បាប់កម្ពុជា។ ចម្លើយនឹងភ្ជាប់ប្រភពច្បាប់ និង PDF ដើម។</p><div className="mt-6 flex flex-wrap justify-center gap-2 text-sm text-slate-600"><button type="button" onClick={() => setInput('តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?')} className="rounded-full border border-slate-200 px-3 py-2 hover:border-blue-300">តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?</button><button type="button" onClick={() => setInput('ស្វែងរកមាត្រា ៨')} className="rounded-full border border-slate-200 px-3 py-2 hover:border-blue-300">ស្វែងរកមាត្រា ៨</button></div></div></div>}
      {messages.map((message, index) => message.role === 'assistant' ? <div key={`${message.role}-${index}`} className="flex items-start gap-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-blue-700 text-xs font-bold text-white">ធី</div><div className="max-w-[90%]"><p className="mb-1 text-xs font-semibold text-blue-700">ធីតា</p><div className="khmer-text whitespace-pre-wrap rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 leading-7 text-slate-800">{message.content}</div></div></div> : <div key={`${message.role}-${index}`} className="flex justify-end"><div className="max-w-[90%]"><p className="mb-1 text-right text-xs font-semibold text-slate-500">អ្នក</p><div className="khmer-text whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-blue-700 px-4 py-3 leading-7 text-white">{message.content}</div></div></div>)}
      {loading && <div className="flex items-start gap-3" aria-label="ធីតាកំពុងវាយ…"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-blue-700 text-xs font-bold text-white">ធី</div><div><p className="mb-1 text-xs font-semibold text-blue-700">ធីតា</p><div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3"><span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-500" /></div></div></div>}
      {error && <div className="space-y-3"><StatePanel title={error} tone="error" /><Button variant="secondary" onClick={() => void send(undefined, lastQuestion, false)}>ព្យាយាមម្តងទៀត</Button></div>}
      {response && !response.hasSufficientEvidence && <StatePanel title="មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់" description={response.insufficientEvidenceMessage ?? undefined} tone="warning" />}
      {response?.hasSufficientEvidence && response.sources.length > 0 && <div className="space-y-3 pt-2"><h2 className="text-lg font-bold">ប្រភពយោង</h2>{response.sources.map((source) => <SourceCard key={`${source.documentId}-${source.articleNumber}`} source={source} compact />)}</div>}
    </div>
    <form onSubmit={(event) => void send(event)} className="mt-4 flex gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-lg shadow-slate-200/50"><textarea value={input} onChange={(event) => setInput(event.target.value)} rows={2} className="flex-1 resize-none rounded-lg border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500" placeholder="សួរសំណួររបស់អ្នក…" aria-label="សំណួររបស់អ្នក" /><Button type="submit" disabled={loading || !input.trim()}>ផ្ញើ</Button></form>
    <p className="pt-3 text-center text-xs text-slate-500">ចម្លើយនេះគឺសម្រាប់ព័ត៌មានប៉ុណ្ណោះ។ សូមពិនិត្យប្រភព PDF ដើម។</p>
  </section>
}
