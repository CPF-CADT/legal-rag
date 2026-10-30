# LegalRAG UI Product Requirements Document

## 1. Product

LegalRAG is a React web application for searching Cambodian legal documents and asking questions about laws. Every answer must show the supporting document, article number, and downloadable original PDF link.

## 2. Goal

Help users find the correct Cambodian legal article quickly and understand it without losing the original legal source.

## 2.1 Frontend technology decisions

- React with TypeScript
- Vite for development and production builds
- Tailwind CSS for styling
- React Router for page navigation
- Feature-oriented folder structure
- Native `fetch` or a small API client for backend requests

The UI should avoid introducing a global state library in the first MVP. Use local React state for page-level state and feature stores only when shared state is necessary.

## 3. Target users

- Lawyers and legal researchers
- Cambodian students
- Government staff
- Members of the public looking for legal information

## 4. MVP scope

### In scope

- Khmer legal keyword search
- Semantic legal search
- Exact lookup by document and article number
- Chat-style legal questions
- Article and chapter browsing
- Source citations for every grounded answer
- Original PDF download/open link
- Search filters and result pagination

### Out of scope for MVP

- Legal advice or legal representation
- User accounts and saved conversations
- Collaborative annotations
- Automatic legal translation
- Document editing

## 5. Main user flow

```text
Open LegalRAG
  ↓
Search or ask a question
  ↓
View ranked legal articles
  ↓
Read article context
  ↓
Open original PDF source
```

For chat:

```text
User question
  ↓
Retrieve relevant articles
  ↓
Generate grounded answer
  ↓
Show answer and source cards
```

## 6. Screens

### 6.1 Home/Search screen

Components:

- LegalRAG logo and application name
- Search input
- Search mode selector: `Keyword`, `Semantic`, `Exact article`
- Language indicator: Khmer
- Recent example queries
- Short disclaimer: “This system provides information, not legal advice.”

Example placeholder:

```text
ស្វែងរកច្បាប់ ឬសួរសំណួរអំពីច្បាប់...
```

### 6.2 Search results screen

Each result card displays:

- Document title
- Article number
- Chapter and section
- Short article excerpt
- Relevance score, if available
- `Read article` button
- `Open PDF` button

Filters:

- Document type
- Category
- Document title
- Chapter
- Article number

### 6.3 Chat screen

Components:

- Conversation message list
- Khmer question input
- Send button
- Clear conversation button
- Loading state
- Evidence/source panel below each answer

Each answer must include:

- Answer text
- Evidence disclaimer when confidence is low
- Source document title
- Article number
- Chapter/section when available
- Clickable PDF download link

### 6.4 Article detail screen

Displays:

- Document title
- Document type and number
- Chapter title
- Section title
- Article number
- Full raw article text
- Previous/next article navigation
- Original PDF link
- Source text metadata

## 6.5 Text-based UI draft

### Home/Search page

```text
┌──────────────────────────────────────────────────────────────┐
│ LegalRAG                                      Khmer Legal AI │
├──────────────────────────────────────────────────────────────┤
│ ស្វែងរកច្បាប់ ឬសួរសំណួរអំពីច្បាប់                           │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ បញ្ចូលសំណួរ ឬពាក្យគន្លឹះ...                    [Search] │ │
│ └──────────────────────────────────────────────────────────┘ │
│ [Keyword] [Semantic] [Exact Article]                         │
│                                                              │
│ ឧទាហរណ៍៖                                                   │
│ • តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?                        │
│ • ស្វែងរកមាត្រា ៨ នៃច្បាប់ចរាចរណ៍                          │
└──────────────────────────────────────────────────────────────┘
```

### Search results page

```text
┌──────────────────────────────────────────────────────────────┐
│ [Search input........................................] [Go]  │
├───────────────┬──────────────────────────────────────────────┤
│ Filters       │ Results for: ប័ណ្ណបើកបរ                      │
│               │                                              │
│ Document      │ ┌──────────────────────────────────────────┐ │
│ [All laws  v] │ │ ច្បាប់ស្តីពីចរាចរណ៍ផ្លូវគោក              │ │
│               │ │ មាត្រា ៨                                  │ │
│ Chapter       │ │ គ្រប់អ្នកបើកបរយានយន្តគ្រប់ប្រភេទ...     │ │
│ [All chapters]│ │ [Read article]             [Open PDF]    │ │
│               │ └──────────────────────────────────────────┘ │
│ Article no.   │                                              │
│ [___________] │ ┌──────────────────────────────────────────┐ │
│               │ │ Another legal result                     │ │
│               │ │ Article number and excerpt...             │ │
│               │ │ [Read article]             [Open PDF]    │ │
└───────────────┴──────────────────────────────────────────────┘
```

### Chat page

```text
┌──────────────────────────────────────────────────────────────┐
│ LegalRAG Chat                              [Clear chat]      │
├──────────────────────────────────────────────────────────────┤
│ User: តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?                    │
│                                                              │
│ LegalRAG:                                                    │
│ ចម្លើយផ្អែកលើមាត្រាដែលបានរកឃើញ...                           │
│                                                              │
│ ប្រភពយោង                                                   │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ច្បាប់ស្តីពីចរាចរណ៍ផ្លូវគោក — មាត្រា ៨                 │ │
│ │ [Read article]                         [Download PDF]    │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ សួរសំណួររបស់អ្នក...                         [Send]     │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Article reader page

```text
┌──────────────────────────────────────────────────────────────┐
│ ← Back to results                              [Open PDF]    │
├──────────────────────────────────────────────────────────────┤
│ ច្បាប់ស្តីពីចរាចរណ៍ផ្លូវគោក                                 │
│ ជំពូកទី ១ · ផ្នែកទី ១ · មាត្រា ៨                           │
├──────────────────────────────────────────────────────────────┤
│ គ្រប់អ្នកបើកបរយានយន្តគ្រប់ប្រភេទ ត្រូវអនុវត្តនូវវិធានការ... │
│                                                              │
│ [Previous article]                         [Next article]    │
└──────────────────────────────────────────────────────────────┘
```

### Responsive mobile layout

On mobile, the filter panel becomes a collapsible button, result cards use the full width, and source actions remain visible below each answer.

## 7. Source citation requirements

The backend response must provide structured sources:

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "1",
      "title": "ច្បាប់ស្តីពីចរាចរផ្លូវគោក",
      "article_number": 8,
      "chapter_title": null,
      "section_title": null,
      "pdf_url": "https://library.ncdd.gov.kh/detail/1/download"
    }
  ]
}
```

The UI must never invent a source URL. If `pdf_url` is missing, show `Source link unavailable`.

## 8. Required UI states

- Initial empty state
- Searching
- Search results
- No results
- Chat response loading
- Chat response with sources
- Chat response without sufficient evidence
- API error
- Broken or unavailable PDF link
- Long article loading

## 9. Grounding and safety behavior

- Only rows with `record_type = article` should be used for legal retrieval.
- Preamble records should not be returned as legal article evidence.
- If no relevant article is retrieved, the assistant must say that it could not find sufficient evidence.
- The UI must display that results are informational and not legal advice.
- Citations must be clickable and tied to the retrieved article.

## 10. Accessibility and usability

- Support Khmer Unicode correctly.
- Use readable Khmer typography and line height.
- Keyboard-accessible search, chat, filters, and source links.
- Visible focus states.
- Sufficient color contrast.
- Responsive layout for desktop and mobile.
- Preserve line breaks in legal article text.

## 11. Suggested React component structure

```text
src/
├── app/
│   ├── App.tsx
│   └── routes.tsx
├── components/
│   ├── SearchBar.tsx
│   ├── SearchFilters.tsx
│   ├── SearchResultCard.tsx
│   ├── ChatMessage.tsx
│   ├── SourceCard.tsx
│   └── ArticleViewer.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── SearchResultsPage.tsx
│   ├── ChatPage.tsx
│   └── ArticlePage.tsx
├── services/
│   └── legalRagApi.ts
└── types/
    └── legal.ts
```

## 12. React frontend folder structure

The UI should use a feature-oriented React structure. The referenced React structure separates reusable components, route-level pages, feature modules, services, state, types, styles, and configuration. This is adapted for LegalRAG from the referenced article: [Recommended Industry-Standard React.js Folder Structure](https://dev.to/pramod_boda/recommended-folder-structure-for-react-2025-48mc).

```text
legalrag-web/
├── public/
│   ├── favicon.svg
│   └── robots.txt
├── src/
│   ├── assets/
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   └── Spinner/
│   │   └── layout/
│   │       ├── Header/
│   │       ├── Sidebar/
│   │       └── MainLayout/
│   ├── features/
│   │   ├── search/
│   │   │   ├── components/
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── SearchFilters.tsx
│   │   │   │   └── SearchResultCard.tsx
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── searchStore.ts
│   │   │   └── index.ts
│   │   ├── chat/
│   │   │   ├── components/
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── SourceCard.tsx
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── chatStore.ts
│   │   │   └── index.ts
│   │   ├── articles/
│   │   │   ├── components/
│   │   │   │   ├── ArticleViewer.tsx
│   │   │   │   └── ArticleNavigation.tsx
│   │   │   ├── services/
│   │   │   └── index.ts
│   │   └── documents/
│   │       ├── components/
│   │       ├── services/
│   │       └── index.ts
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── SearchResultsPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ArticlePage.tsx
│   │   └── NotFoundPage.tsx
│   ├── routes/
│   │   └── AppRoutes.tsx
│   ├── hooks/
│   │   ├── useDebounce.ts
│   │   └── useMediaQuery.ts
│   ├── services/
│   │   ├── apiClient.ts
│   │   └── errorHandler.ts
│   ├── store/
│   │   └── index.ts
│   ├── types/
│   │   ├── article.types.ts
│   │   ├── document.types.ts
│   │   ├── search.types.ts
│   │   └── chat.types.ts
│   ├── utils/
│   │   ├── formatArticle.ts
│   │   └── constants.ts
│   ├── styles/
│   │   ├── globals.css
│   │   ├── variables.css
│   │   └── khmer.css
│   ├── config/
│   │   └── env.ts
│   ├── App.tsx
│   └── main.tsx
├── tests/
│   ├── integration/
│   └── e2e/
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### Structure rules

- Put reusable visual primitives in `components/common`.
- Put shared layout components in `components/layout`.
- Keep search, chat, article, and document logic inside their own `features` folders.
- Keep route-level composition in `pages`.
- Keep API calls close to their feature in `features/*/services`.
- Keep only truly global API/configuration code in `src/services` and `src/config`.
- Keep feature state such as `searchStore.ts` and `chatStore.ts` inside the related feature.
- Keep TypeScript data contracts in `src/types`.
- Add tests beside complex components or in the top-level `tests` directory.

## 13. API requirements

```text
GET  /api/laws
GET  /api/articles/{document_id}/{article_number}
POST /api/search
POST /api/chat
```

Search request:

```json
{
  "query": "តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?",
  "mode": "semantic",
  "filters": {
    "document_id": null,
    "chapter_number": null,
    "article_number": null
  },
  "page": 1,
  "page_size": 10
}
```

## 14. Success criteria

- A user can find an article by document and article number.
- A user can search Khmer legal text and see relevant article results.
- A user can ask a Khmer question and receive an answer grounded in retrieved articles.
- Every grounded answer displays at least one source citation when evidence exists.
- Every source citation includes a working original PDF URL when available.
- Users can open the full article and preserve its original line structure.
- The interface works on desktop and mobile.

## 15. Sequential implementation tasks

### Task 1 — Create the React application

- Create a Vite React TypeScript application.
- Install and configure Tailwind CSS.
- Add the base Khmer font, colors, spacing, and responsive breakpoints.
- Create the root `App.tsx` and `main.tsx` files.

Deliverable: the application starts and displays a basic LegalRAG shell.

### Task 2 — Create the frontend folder structure

- Create `components/common` for reusable controls.
- Create `components/layout` for header and page layout.
- Create feature folders for `search`, `chat`, `articles`, and `documents`.
- Create `pages`, `routes`, `services`, `types`, `hooks`, `utils`, and `config`.

Deliverable: the project structure matches the PRD and imports remain feature-oriented.

### Task 3 — Add React Router navigation

Create these routes:

```text
/
/search
/chat
/articles/:documentId/:articleNumber
```

Add a `NotFoundPage` and shared `MainLayout`.

Deliverable: users can navigate between home, search, chat, and article pages without full-page reloads.

### Task 4 — Build the shared layout with Tailwind CSS

- Build the header with LegalRAG branding.
- Add navigation links for Search and Chat.
- Add a responsive mobile menu.
- Add consistent Khmer typography and readable article spacing.

Deliverable: all pages use the same responsive layout.

### Task 5 — Build the search page

- Add the Khmer search input.
- Add search mode buttons: Keyword, Semantic, and Exact Article.
- Add document, chapter, section, and article filters.
- Add loading, empty, and error states.

Deliverable: the page can submit a search request and display a result list.

### Task 6 — Build search result cards

Each result card must display:

- Document title
- Chapter and section
- Article number
- Article excerpt
- `Read article` action
- `Open PDF` action using the backend-provided `pdf_url`

Deliverable: users can move from search results to an article or its original PDF.

### Task 7 — Build the article reader

- Display document title and legal hierarchy.
- Display article number and raw article text.
- Preserve line breaks with Tailwind whitespace utilities.
- Add previous/next article navigation.
- Add the original PDF link.

Deliverable: users can read the complete source article without text rewriting.

### Task 8 — Connect the search API

Implement the frontend API client for:

```text
GET  /api/laws
GET  /api/articles/{document_id}/{article_number}
POST /api/search
```

Define TypeScript types for requests and responses in `src/types`.

Deliverable: search and article pages use real backend data instead of mock data.

### Task 9 — Build the chat interface

- Build the conversation message list.
- Build the Khmer chat input and send action.
- Add loading and error states.
- Display the assistant answer in a readable Khmer layout.

Deliverable: users can submit a question and see the response.

### Task 10 — Add source citations to chat responses

For every retrieved source, show a `SourceCard` containing:

- Document title
- Article number
- Chapter and section
- Short evidence excerpt
- `Read article` link
- `Download PDF` link

Deliverable: every grounded answer has clickable legal references.

### Task 11 — Add insufficient-evidence behavior

If the backend returns no reliable source:

```text
មិនអាចរកឃើញប្រភពច្បាប់គ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ។
```

Do not display an unsupported legal answer as authoritative.

Deliverable: the UI clearly separates supported answers from unanswered questions.

### Task 12 — Add responsive and accessibility behavior

- Test desktop, tablet, and mobile layouts.
- Add keyboard navigation.
- Add visible focus styles.
- Add labels to inputs and buttons.
- Verify Khmer text wrapping and readable line height.
- Verify PDF links are keyboard accessible.

Deliverable: the MVP is usable on small screens and with keyboard navigation.

### Task 13 — Add frontend tests

Test:

- Route navigation
- Search submission
- Empty search results
- Article rendering
- Chat loading state
- Source citation rendering
- PDF link rendering
- Insufficient-evidence response

Deliverable: critical UI behavior is covered by automated tests.

### Task 14 — Final integration and acceptance test

Run this complete flow:

```text
Open home page
→ Search for a Khmer legal term
→ Open a result
→ Open the original PDF
→ Ask a Khmer question
→ Verify the answer source
→ Open the cited article
→ Download the cited PDF
```

Deliverable: a working React legal search and chatbot MVP.

## 16. MVP acceptance test

1. Search for `ប័ណ្ណបើកបរ`.
2. Confirm results show document title, article number, and article text.
3. Open an article.
4. Click `Open PDF`.
5. Ask a legal question in Khmer.
6. Confirm the answer includes source document and article references.
7. Test a question with no evidence and confirm the system does not invent an answer.
