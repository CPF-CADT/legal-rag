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

  return <section className="mx-auto flex min-h-0 w-full max-w-5xl flex-col bg-white p-0 sm:min-h-[calc(100vh-9rem)] sm:p-6 lg:p-8">
    <div className="flex flex-col gap-3 border-b border-slate-100 px-1 pb-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:border-0 sm:pb-5">
      <div className="flex min-w-0 items-center gap-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-blue-600 text-sm font-black text-white sm:h-10 sm:w-10">ធី</div><div className="min-w-0"><p className="truncate text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500 sm:text-xs sm:tracking-[0.18em]">LegalRAG · Thita</p><h1 className="mt-1 text-xl font-bold text-slate-900 sm:text-3xl">សួរសំណួរអំពីច្បាប់</h1></div></div>
      <div className="flex w-full items-center gap-2 sm:w-auto"><Link to="/search" className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-center text-sm font-semibold text-slate-700 hover:bg-slate-50 sm:flex-none">ស្វែងរកច្បាប់</Link><button type="button" onClick={clear} className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100">សម្អាត</button></div>
    </div>
    <div className="chat-scrollbar min-h-0 flex-1 space-y-5 overflow-visible rounded-2xl bg-white px-0 py-5 sm:overflow-y-auto sm:p-8">
      {messages.length === 0 && <div className="flex min-h-[320px] items-center justify-center px-2 text-center sm:min-h-[420px]"><div className="max-w-xl"><div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-slate-100 text-xl font-black text-blue-600 sm:h-16 sm:w-16 sm:text-2xl">ធី</div><p className="mt-5 text-xs font-bold uppercase tracking-[0.14em] text-slate-500 sm:mt-6 sm:text-sm sm:tracking-[0.18em]">សួស្តី! ខ្ញុំគឺធីតា</p><h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900 sm:text-5xl">តើអ្នកចង់ស្វែងយល់អ្វី?</h2><p className="mt-3 text-sm leading-7 text-slate-600 sm:mt-4 sm:text-base sm:leading-8">សួរអំពីមាត្រា ឬលក្ខខណ្ឌក្នុងច្បាប់កម្ពុជា។ ខ្ញុំនឹងបង្ហាញចម្លើយជាមួយប្រភព PDF ដើម។</p><div className="mt-6 flex flex-col gap-2 text-sm text-slate-600 sm:mt-7 sm:flex-row sm:flex-wrap sm:justify-center"><button type="button" onClick={() => setInput('តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?')} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left transition hover:border-slate-400 hover:bg-slate-50 sm:w-auto sm:rounded-full sm:px-4">តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?</button><button type="button" onClick={() => setInput('ស្វែងរកមាត្រា ៨')} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left transition hover:border-slate-400 hover:bg-slate-50 sm:w-auto sm:rounded-full sm:px-4">ស្វែងរកមាត្រា ៨</button></div></div></div>}
      {messages.map((message, index) => message.role === 'assistant' ? <div key={`${message.role}-${index}`} className="flex min-w-0 items-start gap-2 sm:gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold text-blue-600">ធី</div><div className="min-w-0 max-w-[calc(100%-2.5rem)]"><p className="mb-1 text-xs font-semibold text-slate-500">ធីតា</p><div className="khmer-text break-words whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white px-3 py-3 leading-7 text-slate-800 sm:px-4">{message.content}</div></div></div> : <div key={`${message.role}-${index}`} className="flex min-w-0 justify-end"><div className="min-w-0 max-w-[88%]"><p className="mb-1 text-right text-xs font-semibold text-slate-500">អ្នក</p><div className="khmer-text break-words whitespace-pre-wrap rounded-2xl bg-slate-100 px-3 py-3 leading-7 text-slate-800 sm:px-4">{message.content}</div></div></div>)}
      {loading && <div className="flex items-start gap-2 sm:gap-3" aria-label="ធីតាកំពុងវាយ…"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold text-blue-600">ធី</div><div><p className="mb-1 text-xs font-semibold text-slate-500">ធីតា កំពុងវាយ…</p><div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white px-4 py-3"><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" /></div></div></div>}
      {error && <div className="space-y-3"><StatePanel title={error} tone="error" /><Button variant="secondary" onClick={() => void send(undefined, lastQuestion, false)}>ព្យាយាមម្តងទៀត</Button></div>}
      {response && !response.hasSufficientEvidence && <StatePanel title="មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់" description={response.insufficientEvidenceMessage ?? undefined} tone="warning" />}
      {response?.hasSufficientEvidence && response.sources.length > 0 && <div className="min-w-0 space-y-3 pt-2"><h2 className="text-base font-bold sm:text-lg">ប្រភពយោង</h2>{response.sources.map((source) => <SourceCard key={`${source.documentId}-${source.articleNumber}`} source={source} compact />)}</div>}
    </div>
    <form onSubmit={(event) => void send(event)} className="mt-3 flex flex-col gap-2 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm sm:mt-4 sm:flex-row sm:gap-3 sm:p-3"><textarea value={input} onChange={(event) => setInput(event.target.value)} rows={3} className="min-h-[72px] w-full flex-1 resize-none rounded-xl border-0 bg-transparent px-3 py-2.5 text-base leading-6 outline-none ring-0 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-200 sm:min-h-0 sm:px-4 sm:py-3" placeholder="សួរសំណួររបស់អ្នក…" aria-label="សំណួររបស់អ្នក" /><Button type="submit" disabled={loading || !input.trim()}>ផ្ញើ ↗</Button></form>
    <p className="px-2 pt-2 text-center text-[11px] leading-5 text-slate-400 sm:pt-3 sm:text-xs">ធីតាផ្តល់ព័ត៌មានសម្រាប់ជំនួយប៉ុណ្ណោះ។ សូមពិនិត្យប្រភព PDF ដើម។</p>
  </section>
}
