import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  ChatHeader,
  ChatInputComposer,
  ChatMessageItem,
  ChatSidebar,
  EmptyStateGreeting,
  useChatSessions,
} from '../features/chat'
import { apiClient } from '../services/api'
import { IconRefresh, IconSparkles } from '../components/common/Icons'

export function ChatPage() {
  const {
    sessions,
    activeSession,
    createNewSession,
    selectSession,
    deleteSession,
    clearActiveSession,
    addMessage,
  } = useChatSessions()

  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q')

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [lastQuestion, setLastQuestion] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [activeSession.messages.length, loading])

  const handleSend = async (question = input.trim()) => {
    if (!question || loading) return

    setInput('')
    setError('')
    setLastQuestion(question)

    // Add user message to active session
    addMessage({
      role: 'user',
      content: question,
    })

    setLoading(true)

    try {
      // Build previous conversation history for context
      const history = activeSession.messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await apiClient.chat(question, history)

      const answerContent =
        response.answer ??
        response.insufficientEvidenceMessage ??
        'មិនអាចរកឃើញចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់នៅក្នុងប្រព័ន្ធច្បាប់ទេ។'

      addMessage({
        role: 'assistant',
        content: answerContent,
        sources: response.sources,
        hasSufficientEvidence: response.hasSufficientEvidence,
        insufficientEvidenceMessage: response.insufficientEvidenceMessage,
      })
    } catch {
      setError('ការតភ្ជាប់ទៅកាន់ម៉ាស៊ីនបម្រើបរាជ័យ។ សូមព្យាយាមម្តងទៀត។')
    } finally {
      setLoading(false)
    }
  }

  // Handle URL query parameter `?q=...`
  useEffect(() => {
    if (initialQuery) {
      void handleSend(initialQuery)
      setSearchParams({})
    }
  }, [initialQuery])

  // Global ⌘K / Ctrl+K shortcut for New Chat
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        createNewSession()
      }
    }
    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => window.removeEventListener('keydown', handleGlobalKeyDown)
  }, [createNewSession])

  const handleRetry = () => {
    if (lastQuestion) {
      void handleSend(lastQuestion)
    }
  }

  const hasMessages = activeSession.messages.length > 0

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-slate-900">
      {/* ChatGPT-style Collapsible Light Sidebar */}
      <ChatSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onToggle={() => setSidebarOpen((prev) => !prev)}
        sessions={sessions}
        activeSessionId={activeSession.id}
        onSelectSession={selectSession}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
      />

      {/* Main Chat Viewport */}
      <div className="flex min-w-0 flex-1 flex-col h-full overflow-hidden bg-white">
        {/* Sticky Header */}
        <ChatHeader
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          onClearSession={clearActiveSession}
          canClear={hasMessages}
        />

        {/* Scrollable Message Canvas */}
        <main className="chat-scrollbar flex-1 overflow-y-auto px-4 py-4 sm:px-6">
          <div className="mx-auto flex min-h-full max-w-3xl flex-col justify-between">
            {!hasMessages ? (
              /* Empty state: Chat input is centered directly in the middle */
              <EmptyStateGreeting
                input={input}
                onChange={setInput}
                onSubmit={() => void handleSend()}
                loading={loading}
              />
            ) : (
              /* Active conversation stream */
              <div className="divide-y divide-slate-100/80 space-y-2">
                {activeSession.messages.map((msg) => (
                  <ChatMessageItem key={msg.id} message={msg} />
                ))}

                {/* Loading indicator */}
                {loading && (
                  <div className="flex gap-3 sm:gap-4 py-4" aria-label="ធីតាកំពុងគិត…">
                    <div className="grid h-8 w-8 sm:h-9 sm:w-9 shrink-0 place-items-center rounded-full bg-blue-600 text-white shadow-sm">
                      <IconSparkles className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-2 pt-1 text-xs sm:text-sm text-slate-500">
                      <span>ធីតាកំពុងស្វែងរក និងវិភាគច្បាប់</span>
                      <span className="flex items-center gap-1">
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                      </span>
                    </div>
                  </div>
                )}

                {/* Error Panel */}
                {error && (
                  <div className="my-4 rounded-xl border border-red-200 bg-red-50 p-4 text-xs sm:text-sm text-red-800">
                    <p className="font-semibold">{error}</p>
                    <button
                      type="button"
                      onClick={handleRetry}
                      className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 shadow-sm"
                    >
                      <IconRefresh className="h-3.5 w-3.5" />
                      <span>ព្យាយាមម្តងទៀត</span>
                    </button>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Pinned Bottom Input Dock - only shown during active conversation */}
        {hasMessages && (
          <footer className="w-full shrink-0 bg-white pt-2 border-t border-slate-100/60 sm:border-0">
            <ChatInputComposer
              input={input}
              onChange={setInput}
              onSubmit={() => void handleSend()}
              loading={loading}
              variant="bottom"
            />
          </footer>
        )}
      </div>
    </div>
  )
}
