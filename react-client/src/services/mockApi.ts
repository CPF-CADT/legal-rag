import type { ApiClient, ChatMessageInput, Citation, LegalArticle, SearchResult } from '../types'

const pdfUrl = 'https://library.ncdd.gov.kh/detail/1/download'
const baseArticle = {
  documentId: '1',
  documentType: 'Law',
  documentNumber: null,
  title: 'ច្បាប់ស្តីពីចរាចរណ៍ផ្លូវគោក (វិសោធនកម្ម)',
  category: 'ចរាចរណ៍',
  issuedDate: '2017-01-26',
  chapterNumber: null,
  chapterTitle: null,
  sectionNumber: null,
  sectionTitle: null,
  pdfUrl,
  sequence: 1,
  recordType: 'article' as const,
  reviewRequired: false,
  reviewReason: null,
}

const articles: LegalArticle[] = [
  {
    ...baseArticle,
    articleNumber: '8',
    articleText: `គ្រប់អ្នកបើកបរយានយន្តគ្រប់ប្រភេទ ត្រូវអនុវត្តនូវវិធានការដូចតទៅ៖
១- ត្រូវមានប័ណ្ណបើកបរចំពោះអ្នកបើកបរយានយន្តដូចខាងក្រោម៖
-ទោចក្រយានយន្តសណ្ដោងរ៉ឺម៉ក និងត្រីចក្រយានយន្ត
-យានយន្តដែលមានទំហំស៊ីឡាំងលើសពី ១២៥ សង់ទីម៉ែត្រគូប ឡើងទៅ។`,
  },
  {
    ...baseArticle,
    articleNumber: '40',
    sequence: 2,
    articleText: `ប័ណ្ណបើកបរជាតិសម្រាប់បើកបរយានយន្តក្នុងព្រះរាជាណាចក្រកម្ពុជា មាន ៥ (ប្រាំ) ប្រភេទដូចខាងក្រោម៖
ប្រភេទក៖ ទោចក្រយានយន្ត ដែលមានទំហំស៊ីឡាំងលើសពី ១២៥ សង់ទីម៉ែត្រគូប ឬមានថាមពលអគ្គិសនីលើសពី ១១ គីឡូវ៉ាត់។`,
  },
  {
    ...baseArticle,
    articleNumber: '41',
    sequence: 3,
    articleText: 'លក្ខខណ្ឌផ្សេងៗទាក់ទងនឹងប័ណ្ណបើកបរ ត្រូវកំណត់ដូចខាងក្រោម៖',
  },
]

const normalize = (value: string) => value.toLowerCase().replace(/\s+/g, ' ').trim()

const toCitation = (article: LegalArticle, score: number | null = null): Citation => ({
  ...article,
  excerpt: article.articleText.length > 220 ? `${article.articleText.slice(0, 220)}…` : article.articleText,
  score,
})

const toSearchResult = (article: LegalArticle, score: number | null): SearchResult => ({
  ...article,
  excerpt: article.articleText.length > 220 ? `${article.articleText.slice(0, 220)}…` : article.articleText,
  score,
})

export const mockApiClient: ApiClient = {
  async getLaws() {
    const unique = articles.filter((article, index, list) => list.findIndex((item) => item.documentId === article.documentId) === index)
    return { items: unique.map((article) => ({ documentId: article.documentId, documentType: article.documentType, documentNumber: article.documentNumber, title: article.title, issuedDate: article.issuedDate, pdfUrl: article.pdfUrl, reviewRequired: article.reviewRequired })), pagination: { page: 1, pageSize: 20, total: unique.length, totalPages: 1 } }
  },
  async getArticle(documentId, articleNumber) {
    await new Promise((resolve) => window.setTimeout(resolve, 250))
    const index = articles.findIndex((article) => article.documentId === documentId && article.articleNumber === articleNumber)
    if (index < 0) return null
    return { article: articles[index], navigation: { previousArticleNumber: articles[index - 1]?.articleNumber ?? null, nextArticleNumber: articles[index + 1]?.articleNumber ?? null } }
  },
  async search(request) {
    await new Promise((resolve) => window.setTimeout(resolve, 350))
    const query = normalize(request.query)
    const matches = articles.filter((article) => {
      if (request.filters?.articleNumber && article.articleNumber !== request.filters.articleNumber) return false
      if (request.filters?.documentType && article.documentType !== request.filters.documentType) return false
      if (request.filters?.documentTitle && !normalize(article.title).includes(normalize(request.filters.documentTitle))) return false
      if (request.filters?.category && article.category !== request.filters.category) return false
      if (request.filters?.chapterNumber && article.chapterNumber !== request.filters.chapterNumber) return false
      if (request.mode === 'exact_article') return article.articleNumber === request.filters?.articleNumber
      if (!query) return true
      return normalize(`${article.title} ${article.articleText}`).includes(query) || (query.includes('ប័ណ្ណ') && article.articleNumber === '8')
    })
    const page = Math.max(request.page ?? 1, 1)
    const pageSize = Math.max(request.pageSize ?? 10, 1)
    const start = (page - 1) * pageSize
    const items = matches.slice(start, start + pageSize).map((article, index) => toSearchResult(article, Math.max(0.96 - (start + index) * 0.08, 0.72)))
    return { query: request.query, mode: request.mode, items, pagination: { page, pageSize, total: matches.length, totalPages: Math.max(Math.ceil(matches.length / pageSize), 1) }, hasSufficientEvidence: matches.length > 0 }
  },
  async chat(message: string, _conversation: ChatMessageInput[] = []) {
    await new Promise((resolve) => window.setTimeout(resolve, 550))
    const result = await this.search({ query: message, mode: 'semantic', page: 1, pageSize: 5 })
    if (!result.hasSufficientEvidence) return { answer: null, sources: [], hasSufficientEvidence: false, insufficientEvidenceMessage: 'មិនមានប្រភពច្បាប់គ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ។ សូមសាកល្បងប្រើពាក្យគន្លឹះផ្សេងទៀត។' }
    return { answer: 'តាមមាត្រាដែលបានរកឃើញ អ្នកបើកបរយានយន្តប្រភេទដែលច្បាប់កំណត់ ត្រូវមានប័ណ្ណបើកបរ។ សូមអានប្រភពដើមសម្រាប់លក្ខខណ្ឌពេញលេញ។', sources: result.items.slice(0, 2).map(toCitation), hasSufficientEvidence: true, insufficientEvidenceMessage: null }
  },
}
