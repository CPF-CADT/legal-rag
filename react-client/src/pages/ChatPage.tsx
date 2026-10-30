import { FormEvent, useState } from 'react'
import { Button, LoadingPanel, SourceCard, StatePanel } from '../components/common/UI'
import { apiClient } from '../services/api'
import type { ChatMessageInput, ChatResponse } from '../types'

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageInput[]>([])
  const [input, setInput] = useState('')
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastQuestion, setLastQuestion] = useState('')

  const send = async (event?: FormEvent, question = input.trim()) => {
    event?.preventDefault()
    if (!question || loading) return
    if (!lastQuestion) setMessages((items) => [...items, { role: 'user', content: question }])
    setLastQuestion(question); setInput(''); setError(''); setLoading(true)
    try {
      const next = await apiClient.chat(question, messages)
      setResponse(next)
      if (next.answer) setMessages((items) => [...items, { role: 'assistant', content: next.answer! }])
    } catch { setError('ការស្នើសុំបរាជ័យ។ សូមព្យាយាមម្តងទៀត។') } finally { setLoading(false) }
  }

  const clear = () => { setMessages([]); setResponse(null); setError(''); setLastQuestion('') }
  return <section className="mx-auto max-w-4xl space-y-5"><div className="flex items-center justify-between"><div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">LegalRAG Chat</p><h1 className="mt-1 text-3xl font-bold">សួរសំណួរអំពីច្បាប់</h1></div><Button variant="ghost" onClick={clear}>សម្អាតការសន្ទនា</Button></div><div className="min-h-[360px] rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">{messages.length === 0 && <div className="flex h-72 items-center justify-center text-center text-slate-500"><div><p className="text-lg font-semibold text-slate-700">តើអ្នកចង់ស្វែងយល់អ្វី?</p><p className="mt-2 text-sm">សួរអំពីមាត្រា ឬលក្ខខណ្ឌដែលមានក្នុងច្បាប់។</p></div></div>}{messages.map((message, index) => <div key={`${message.role}-${index}`} className={`mb-4 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}><div className={`khmer-text max-w-[90%] whitespace-pre-wrap rounded-2xl px-4 py-3 leading-7 ${message.role === 'user' ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-800'}`}>{message.content}</div></div>)}{loading && <LoadingPanel />}{error && <div className="space-y-3"><StatePanel title={error} tone="error" /><Button variant="secondary" onClick={() => void send(undefined, lastQuestion)}>ព្យាយាមម្តងទៀត</Button></div>}{response && !response.hasSufficientEvidence && <StatePanel title="មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់" description={response.insufficientEvidenceMessage ?? undefined} tone="warning" />}</div>{response?.hasSufficientEvidence && response.sources.length > 0 && <div className="space-y-3"><h2 className="text-lg font-bold">ប្រភពយោង</h2>{response.sources.map((source) => <SourceCard key={`${source.documentId}-${source.articleNumber}`} source={source} />)}</div>}<form onSubmit={(event) => void send(event)} className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"><textarea value={input} onChange={(event) => setInput(event.target.value)} rows={2} className="flex-1 resize-none rounded-lg border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500" placeholder="សួរសំណួររបស់អ្នក…" aria-label="សំណួររបស់អ្នក" /><Button type="submit" disabled={loading || !input.trim()}>ផ្ញើ</Button></form><p className="text-center text-xs text-slate-500">ចម្លើយនេះគឺសម្រាប់ព័ត៌មានប៉ុណ្ណោះ។ សូមពិនិត្យប្រភព PDF ដើម។</p></section>
}
