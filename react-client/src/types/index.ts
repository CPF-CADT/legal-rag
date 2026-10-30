export type Id = string

export type SearchMode = 'keyword' | 'semantic' | 'exact_article'
export type RecordType = 'article' | 'preamble'

export interface LegalSource {
  documentId: Id
  documentType: string | null
  documentNumber: string | null
  title: string
  issuedDate: string | null
  chapterNumber: string | null
  chapterTitle: string | null
  sectionNumber: string | null
  sectionTitle: string | null
  articleNumber: string | null
  pdfUrl: string | null
  sequence: number | null
  recordType: RecordType
  reviewRequired: boolean
  reviewReason: string | null
}

export interface LegalArticle extends LegalSource {
  articleText: string
}

export interface Citation extends LegalSource {
  articleText?: string
  excerpt?: string
  score?: number | null
}

export interface Pagination {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface SearchFilters {
  documentId?: Id | null
  documentType?: string | null
  chapterNumber?: string | null
  sectionNumber?: string | null
  articleNumber?: string | null
}

export interface SearchRequest {
  query: string
  mode: SearchMode
  filters?: SearchFilters
  page?: number
  pageSize?: number
}

export interface SearchResult extends Citation {
  articleText: string
  excerpt: string
  score: number | null
}

export interface SearchResponse {
  query: string
  mode: SearchMode
  items: SearchResult[]
  pagination: Pagination
  hasSufficientEvidence: boolean
}

export interface ChatMessageInput {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  answer: string | null
  sources: Citation[]
  hasSufficientEvidence: boolean
  insufficientEvidenceMessage: string | null
}

export interface ArticleResponse {
  article: LegalArticle
  navigation: {
    previousArticleNumber: string | null
    nextArticleNumber: string | null
  }
}
