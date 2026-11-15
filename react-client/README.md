# LegalRAG React Client

LegalRAG UI built with React, TypeScript, Vite, Tailwind CSS, and React Router. The client runs with mock legal data by default, so it can be developed and demonstrated without a backend.

```bash
npm install
npm run dev
```

Routes include `/`, `/search`, `/chat`, and `/articles/:documentId/:articleNumber`.

## Mock mode

Mock mode is enabled by default. It supports:

- Keyword, semantic, and exact-article search
- Document, category, chapter, and article filters
- Search pagination
- Article reading and previous/next navigation
- Multi-turn chat responses
- Source citations and original PDF links
- Loading, empty, error, retry, and insufficient-evidence states

To connect the real backend later, create `.env` with:

```bash
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
```

The backend must implement the routes documented in `../docs/REACT_CLIENT_API_CONTRACT.md`.

## DOMROV workspace

The frontend now uses DOMROV branding and a Khmer-first workspace. Additional routes:
`/procedures`, `/procedures/:id`, `/saved`. Procedure content is explicitly unreviewed
fixture data in both API modes. Checklists are device-local; conversations remain
in memory only. Print/Save as PDF is available on procedure detail.

See [DOMROV handover](../docs/DOMROV_HANDOVER.md) for implementation, backend dependencies,
validation commands and screenshots. Build with `npm run build`; type-check with
`npm run lint` (the existing script runs TypeScript, not ESLint).
