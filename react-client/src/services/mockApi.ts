import type {
  ArticleResponse,
  ChatMessageInput,
  ChatResponse,
  Citation,
  LegalArticle,
  SearchRequest,
  SearchResult,
  SearchResponse,
} from '../types'

const pdfUrl = 'https://library.ncdd.gov.kh/detail/1/download'
const baseArticle = {
  documentId: '1',
  documentType: 'Law',
  documentNumber: null,
  title: 'ច្បាប់ស្តីពីចរាចរណ៍ផ្លូវគោក (វិសោធនកម្ម)',
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

export async function searchArticles(request: SearchRequest): Promise<SearchResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 350))
  const query = normalize(request.query)
  const matches = articles.filter((article) => {
    if (request.filters?.articleNumber && article.articleNumber !== request.filters.articleNumber) return false
    if (request.mode === 'exact_article') return article.articleNumber === request.filters?.articleNumber
    if (!query) return true
    return normalize(`${article.title} ${article.articleText}`).includes(query) ||
      (query.includes('ប័ណ្ណ') && article.articleNumber === '8')
  })
  const items = matches.map((article, index) => toSearchResult(article, Math.max(0.96 - index * 0.08, 0.72)))
  return {
    query: request.query,
    mode: request.mode,
    items,
    pagination: { page: 1, pageSize: 10, total: items.length, totalPages: 1 },
    hasSufficientEvidence: items.length > 0,
  }
}

export async function getArticle(documentId: string, articleNumber: string): Promise<ArticleResponse | null> {
  await new Promise((resolve) => window.setTimeout(resolve, 250))
  const index = articles.findIndex((article) => article.documentId === documentId && article.articleNumber === articleNumber)
  if (index < 0) return null
  return {
    article: articles[index],
    navigation: {
      previousArticleNumber: articles[index - 1]?.articleNumber ?? null,
      nextArticleNumber: articles[index + 1]?.articleNumber ?? null,
    },
  }
}

export async function askChat(message: string, _conversation: ChatMessageInput[] = []): Promise<ChatResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 550))
  const result = await searchArticles({ query: message, mode: 'semantic', page: 1, pageSize: 5 })
  if (!result.hasSufficientEvidence) {
    return {
      answer: null,
      sources: [],
      hasSufficientEvidence: false,
      insufficientEvidenceMessage: 'មិនមានប្រភពច្បាប់គ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ។ សូមសាកល្បងប្រើពាក្យគន្លឹះផ្សេងទៀត។',
    }
  }
  return {
    answer: 'តាមមាត្រាដែលបានរកឃើញ អ្នកបើកបរយានយន្តប្រភេទដែលច្បាប់កំណត់ ត្រូវមានប័ណ្ណបើកបរ។ សូមអានប្រភពដើមសម្រាប់លក្ខខណ្ឌពេញលេញ។',
    sources: result.items.slice(0, 2).map(toCitation),
    hasSufficientEvidence: true,
    insufficientEvidenceMessage: null,
  }
}
