import type {
  ApiClient,
  ArticleResponse,
  ChatMessageInput,
  ChatResponse,
  Citation,
  FilterOptions,
  LawsQuery,
  LawsResponse,
  SearchRequest,
  SearchResponse,
  SearchResult,
  SearchFilters,
} from '../types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { error?: { message?: string } } | null
    throw new Error(payload?.error?.message ?? `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

type ApiMatchedChunk = {
  chunk_id: string
  text: string
  similarity: number
}

type ApiSearchItem = {
  rank: number
  article_id: string
  document_id: string
  title: string
  article_number: string
  chapter_number: string
  chapter_title: string
  article_text: string
  source_url: string
  pdf_url: string
  score: number
  matched_chunks: ApiMatchedChunk[]
}

type ApiSearchResponse = {
  query: string
  items: ApiSearchItem[]
  count: number
}

type ApiSummarizeResponse = {
  query: string
  summary: string | null
  sources: ApiSearchItem[]
  has_sufficient_evidence: boolean
}

const toCitation = (item: ApiSearchItem): Citation => ({
  documentId: item.document_id,
  documentType: null,
  documentNumber: null,
  title: item.title,
  category: null,
  issuedDate: null,
  chapterNumber: item.chapter_number || null,
  chapterTitle: item.chapter_title || null,
  sectionNumber: null,
  sectionTitle: null,
  articleNumber: item.article_number,
  pdfUrl: item.pdf_url || item.source_url || null,
  sequence: item.rank,
  recordType: 'article',
  reviewRequired: false,
  reviewReason: null,
  articleText: item.article_text,
  excerpt: item.matched_chunks[0]?.text || item.article_text,
  score: item.score,
})

const toSearchResult = (item: ApiSearchItem): SearchResult => toCitation(item) as SearchResult

const toSearchResponse = (response: ApiSearchResponse, request: SearchRequest): SearchResponse => {
  const page = Math.max(request.page ?? 1, 1)
  const pageSize = Math.max((request.pageSize ?? request.top_k ?? response.count) || 1, 1)
  return {
    query: response.query,
    mode: request.mode,
    items: response.items.map(toSearchResult),
    pagination: {
      page,
      pageSize,
      total: response.count,
      totalPages: Math.max(Math.ceil(response.count / pageSize), 1),
    },
    hasSufficientEvidence: response.items.length > 0,
  }
}

export const fetchApiClient: ApiClient = {
  getFilterOptions: async (): Promise<FilterOptions> => request<FilterOptions>('/api/filters'),
  getLaws: async (_query: LawsQuery = {}): Promise<LawsResponse> => {
    throw new Error('The FastAPI MVP does not provide a laws listing endpoint yet.')
  },
  getArticle: async (documentId, articleNumber): Promise<ArticleResponse | null> => {
    const response = await fetchApiClient.search({
      query: articleNumber,
      mode: 'exact_article',
      filters: { documentId, articleNumber },
      page: 1,
      pageSize: 20,
      top_k: 20,
    })
    const match = response.items.find((item) => item.documentId === documentId && item.articleNumber === articleNumber)
    if (!match) return null
    return {
      article: match,
      navigation: { previousArticleNumber: null, nextArticleNumber: null },
    }
  },
  search: async (body: SearchRequest): Promise<SearchResponse> => {
    const response = await request<ApiSearchResponse>('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query: body.query,
        top_k: body.top_k ?? Math.min(body.pageSize ?? 10, 20),
        filters: {
          title: body.filters?.documentTitle || undefined,
          chapter_number: body.filters?.chapterNumber || undefined,
          article_number: body.filters?.articleNumber || undefined,
        },
      }),
    })
    return toSearchResponse(response, body)
  },
  chat: async (message: string, _conversation: ChatMessageInput[] = [], _filters?: SearchFilters): Promise<ChatResponse> => {
    const response = await request<ApiSummarizeResponse>('/api/summarize', {
      method: 'POST',
      body: JSON.stringify({ query: message, top_k: 5 }),
    })
    return {
      answer: response.summary,
      sources: response.sources.map(toCitation),
      hasSufficientEvidence: response.has_sufficient_evidence,
      insufficientEvidenceMessage: response.has_sufficient_evidence ? null : 'មិនមានប្រភពច្បាប់គ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ។ សូមសាកល្បងប្រើពាក្យគន្លឹះផ្សេងទៀត។',
    }
  },
}
