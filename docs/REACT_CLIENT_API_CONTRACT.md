# LegalRAG React Client API Contract

This document defines the browser-facing TypeScript contracts for the React client. It is derived from `docs/UI_PRD.md` and the current `data/processed/legal_articles.csv` schema.

The CSV currently contains these source fields:

```text
document_id, document_type, document_number, title, category, issued_date,
sequence, record_type, chapter_number, chapter_title, section_number,
section_title, article_number, article_text, pdf_url, local_pdf_path,
source_text_path, review_required, review_reason
```

`local_pdf_path` and `source_text_path` are server-side pipeline paths. They must not be sent to or rendered by the browser. `pdf_url` is the public source link used for citations and download/open actions.

## 1. Shared TypeScript types

The frontend should define these types in `src/types/`.

```ts
export type Id = string;

export type SearchMode = "keyword" | "semantic" | "exact_article";

export type RecordType = "article" | "preamble";

export interface LegalSource {
  documentId: Id;
  documentType: string | null;
  documentNumber: string | null;
  title: string;
  category: string | null;
  issuedDate: string | null; // ISO date when known; otherwise null
  chapterNumber: string | null;
  chapterTitle: string | null;
  sectionNumber: string | null;
  sectionTitle: string | null;
  articleNumber: string | null;
  pdfUrl: string | null;
  sequence: number | null;
  recordType: RecordType;
  reviewRequired: boolean;
  reviewReason: string | null;
}

export interface LegalArticle extends LegalSource {
  articleText: string;
}

export interface Citation extends LegalSource {
  articleText?: string;
  excerpt?: string;
  score?: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  requestId?: string;
}

export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
```

The API uses camelCase JSON names. The backend may map them from the snake-case CSV names.

`articleNumber`, chapter numbers, and section numbers are strings because OCR can contain Arabic or Khmer numerals and values such as amended/article labels. The client must not parse them into JavaScript numbers.

## 2. `GET /api/laws`

Returns the document-level list used by filters and document browsing.

### Query parameters

All parameters are optional.

```ts
interface LawsQuery {
  page?: number;
  pageSize?: number;
  documentType?: string;
  query?: string;
}
```

Example request:

```text
GET /api/laws?page=1&pageSize=20&documentType=Law
```

### Response `200 OK`

```ts
interface LawSummary {
  documentId: Id;
  documentType: string | null;
  documentNumber: string | null;
  title: string;
  category: string | null;
  issuedDate: string | null;
  pdfUrl: string | null;
  reviewRequired: boolean;
}

interface LawsResponse {
  items: LawSummary[];
  pagination: Pagination;
}
```

Only documents with at least one usable source record should normally be listed. A missing `pdfUrl` is valid and must be represented as `null`.

## 3. `GET /api/articles/{document_id}/{article_number}`

Returns one complete article for the article reader. The route value must be URL encoded because Khmer article identifiers may be used.

Example:

```text
GET /api/articles/1/%E1%9F%A8
```

### Response `200 OK`

```ts
interface ArticleResponse {
  article: LegalArticle;
  navigation: {
    previousArticleNumber: string | null;
    nextArticleNumber: string | null;
  };
}
```

The article response must contain the complete raw `articleText` in source order. It must not include the CSV's `local_pdf_path` or `source_text_path`.

### Errors

- `400 Bad Request`: invalid or missing route values.
- `404 Not Found`: document or article does not exist.
- `500 Internal Server Error`: backend failure.

Error body:

```ts
interface ErrorResponse {
  error: ApiError;
}
```

## 4. `POST /api/search`

Searches legal articles. Retrieval must exclude `recordType = "preamble"`; preambles may remain available for audit but must not be returned as article evidence.

### Request

```ts
interface SearchFilters {
  documentId?: Id | null;
  documentType?: string | null;
  documentTitle?: string | null;
  category?: string | null;
  chapterNumber?: string | null;
  sectionNumber?: string | null;
  articleNumber?: string | null;
}

interface SearchRequest {
  query: string;
  mode: SearchMode;
  filters?: SearchFilters;
  page?: number;
  pageSize?: number;
}
```

Validation rules:

- `query` is required and must not be blank.
- `mode` must be `keyword`, `semantic`, or `exact_article`.
- `exact_article` should require enough document/article information to identify an article, or return a clear validation error.
- `pageSize` should have a server-enforced maximum.

Example request:

```json
{
  "query": "តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?",
  "mode": "semantic",
  "filters": {
    "documentId": null,
    "chapterNumber": null,
    "sectionNumber": null,
    "articleNumber": null
  },
  "page": 1,
  "pageSize": 10
}
```

### Response `200 OK`

```ts
interface SearchResult extends Citation {
  articleText: string;
  excerpt: string;
  score: number | null;
}

interface SearchResponse {
  query: string;
  mode: SearchMode;
  items: SearchResult[];
  pagination: Pagination;
  hasSufficientEvidence: boolean;
}
```

`articleText` is the raw article body supplied by the extraction pipeline. The UI may display `excerpt` in a result card and use `articleText` on the article page.

## 5. `POST /api/chat`

Answers a legal question using retrieved legal articles. The server is responsible for retrieval and grounding; the client only renders the returned answer and citations.

### Request

```ts
interface ChatMessageInput {
  role: "user" | "assistant";
  content: string;
}

interface ChatRequest {
  message: string;
  conversation?: ChatMessageInput[];
  filters?: SearchFilters;
}
```

The client should send the current user message. Conversation history is optional and should be bounded by the backend contract.

### Response `200 OK`

```ts
interface ChatResponse {
  answer: string | null;
  sources: Citation[];
  hasSufficientEvidence: boolean;
  insufficientEvidenceMessage: string | null;
}
```

Grounding rules:

- `sources` must contain only retrieved legal article records, never preambles.
- If `hasSufficientEvidence` is `false`, `answer` should be `null` or a clearly marked refusal supplied by the backend.
- The client must show `insufficientEvidenceMessage` when present.
- The client must not invent citations, article numbers, titles, or links.

## 6. Source citation and PDF behavior

Every displayed source card should use the returned fields:

```ts
interface SourceCardProps {
  source: Citation;
}
```

Display at minimum:

```text
{title} — មាត្រា {articleNumber}
{chapterTitle, when present}
{sectionTitle, when present}
```

PDF behavior:

1. If `pdfUrl` is a non-empty absolute `http` or `https` URL, render an external link with `href={pdfUrl}`.
2. Use `target="_blank"` and `rel="noreferrer"` for an external source.
3. Label the action `Open original PDF` or `Download original PDF` according to the product wording; do not proxy or rewrite the URL in the React client.
4. If `pdfUrl` is `null` or invalid, do not render a dead link. Show `Source link unavailable` and keep the legal citation visible.
5. Never expose or use `localPdfPath` or `sourceTextPath` in browser URLs.

The source link must come from the API response. The client must never construct a URL from `documentId` or `detailUrl`.

## 7. Loading, empty, error, and evidence states

Each request should expose an explicit UI state rather than relying on an empty array alone.

```ts
type RequestStatus = "idle" | "loading" | "success" | "error";

interface AsyncState<T> {
  status: RequestStatus;
  data: T | null;
  error: ApiError | null;
}
```

Required behavior:

| State | UI behavior |
|---|---|
| Idle | Show the initial prompt or example query. |
| Loading | Disable duplicate submission, show a spinner/skeleton, and preserve the submitted query. |
| Success with items | Render results or the answer and source cards. |
| Success with no results | Show `No relevant legal articles found.` and allow a new query. |
| Chat insufficient evidence | Show the backend evidence message; do not present an unsupported legal answer. |
| API error | Show a concise retryable error and keep the user's query/message. |
| PDF unavailable | Keep citation metadata visible and show `Source link unavailable`. |
| Article not found | Show a not-found state with a link back to search. |

## 8. Small mock JSON response

The following response is suitable for a frontend mock or MSW fixture:

```json
{
  "query": "តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?",
  "mode": "semantic",
  "items": [
    {
      "documentId": "1",
      "documentType": "Law",
      "documentNumber": "នស/រកម/០១១៧/០០២",
      "title": "ច្បាប់ស្តីពីចរាចរផ្លូវគោក (វិសោធនកម្ម)",
      "issuedDate": null,
      "chapterNumber": null,
      "chapterTitle": null,
      "sectionNumber": null,
      "sectionTitle": null,
      "articleNumber": "8",
      "articleText": "គ្រប់អ្នកបើកបរយានយន្តគ្រប់ប្រភេទ ត្រូវអនុវត្តនូវវិធានការដូចតទៅ៖...",
      "excerpt": "គ្រប់អ្នកបើកបរយានយន្តគ្រប់ប្រភេទ ត្រូវអនុវត្តនូវវិធានការដូចតទៅ៖...",
      "pdfUrl": "https://library.ncdd.gov.kh/detail/1/download",
      "sequence": 2,
      "recordType": "article",
      "reviewRequired": false,
      "reviewReason": null,
      "score": 0.94
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "total": 1,
    "totalPages": 1
  },
  "hasSufficientEvidence": true
}
```

## 9. React client implementation notes

- Put shared interfaces in `src/types` and feature-specific request functions in `features/*/services` as specified by the PRD.
- Keep API base URL in configuration, for example `VITE_API_BASE_URL`; do not hard-code an environment-specific host in components.
- Check `response.ok` before parsing a successful response. Parse `ErrorResponse` for non-2xx responses when available.
- Preserve Khmer text and line breaks with CSS such as `white-space: pre-wrap` in article views.
- Use `recordType === "article"` as a defensive client-side check before rendering legal evidence, even though the backend must already filter preambles.
