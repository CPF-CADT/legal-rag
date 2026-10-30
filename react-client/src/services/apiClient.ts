import type { ApiClient, ArticleResponse, ChatMessageInput, ChatResponse, LawsQuery, LawsResponse, SearchRequest, SearchResponse, SearchFilters } from '../types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { error?: { message?: string } } | null
    throw new Error(payload?.error?.message ?? `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

const queryString = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== '') search.set(key, String(value)) })
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const fetchApiClient: ApiClient = {
  getLaws: (query: LawsQuery = {}) => request<LawsResponse>(`/api/laws${queryString({ page: query.page, pageSize: query.pageSize, documentType: query.documentType, query: query.query })}`),
  getArticle: (documentId, articleNumber) => request<ArticleResponse>(`/api/articles/${encodeURIComponent(documentId)}/${encodeURIComponent(articleNumber)}`),
  search: (body: SearchRequest) => request<SearchResponse>('/api/search', { method: 'POST', body: JSON.stringify(body) }),
  chat: (message: string, conversation: ChatMessageInput[] = [], filters?: SearchFilters) => request<ChatResponse>('/api/chat', { method: 'POST', body: JSON.stringify({ message, conversation, filters }) }),
}
