import { useCallback, useEffect, useState } from 'react'
import type { ChatSession, UIMessage } from '../../../types'

const STORAGE_KEY = 'legalrag_chat_sessions_v1'

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

function createEmptySession(title = 'កិច្ចសន្ទនាថ្មី'): ChatSession {
  const now = Date.now()
  return {
    id: generateId(),
    title,
    messages: [],
    createdAt: now,
    updatedAt: now,
  }
}

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as ChatSession[]
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed
        }
      }
    } catch {
      // fallback to initial
    }
    return [createEmptySession()]
  })

  const [activeId, setActiveId] = useState<string>(() => sessions[0]?.id ?? '')

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
    } catch {
      // ignore storage write errors
    }
  }, [sessions])

  const activeSession = sessions.find((s) => s.id === activeId) ?? sessions[0] ?? createEmptySession()

  const createNewSession = useCallback(() => {
    const newSession = createEmptySession()
    setSessions((prev) => [newSession, ...prev])
    setActiveId(newSession.id)
    return newSession.id
  }, [])

  const selectSession = useCallback((id: string) => {
    setActiveId(id)
  }, [])

  const deleteSession = useCallback((id: string) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id)
      if (filtered.length === 0) {
        const fresh = createEmptySession()
        setActiveId(fresh.id)
        return [fresh]
      }
      if (id === activeId) {
        setActiveId(filtered[0].id)
      }
      return filtered
    })
  }, [activeId])

  const clearActiveSession = useCallback(() => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== activeSession.id) return s
        return {
          ...s,
          title: 'កិច្ចសន្ទនាថ្មី',
          messages: [],
          updatedAt: Date.now(),
        }
      })
    )
  }, [activeSession.id])

  const addMessage = useCallback(
    (input: Omit<UIMessage, 'id' | 'createdAt'>): UIMessage => {
      const now = Date.now()
      const newMessage: UIMessage = {
        ...input,
        id: generateId(),
        createdAt: now,
      }

      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== activeSession.id) return s

          const isFirstUserMessage = s.messages.length === 0 && input.role === 'user'
          const title = isFirstUserMessage
            ? input.content.slice(0, 36).trim() + (input.content.length > 36 ? '…' : '')
            : s.title

          return {
            ...s,
            title,
            messages: [...s.messages, newMessage],
            updatedAt: now,
          }
        })
      )

      return newMessage
    },
    [activeSession.id]
  )

  const updateMessage = useCallback(
    (messageId: string, updates: Partial<UIMessage>) => {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== activeSession.id) return s
          return {
            ...s,
            messages: s.messages.map((m) => (m.id === messageId ? { ...m, ...updates } : m)),
            updatedAt: Date.now(),
          }
        })
      )
    },
    [activeSession.id]
  )

  return {
    sessions,
    activeSession,
    createNewSession,
    selectSession,
    deleteSession,
    clearActiveSession,
    addMessage,
    updateMessage,
  }
}

