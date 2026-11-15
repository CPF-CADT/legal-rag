# DOMROV frontend handover

Implemented on `feature/domrov-workspace`; no deployment or merge.

## Repository audit

The actual frontend is `react-client/`, not `apps/react-client/`. No AGENTS.md exists in this checkout or its ancestor directories. Read the task, frontend README, API contract, UI PRD, project guide and project plan. The task's source audit described components/hooks absent from this checkout: no CitationDrawer or useChatSessions exists. Reused the actual ChatPage, SourceCard, PdfLink, search page, article reader, React Router and existing fetch/mock clients.

Design reference: [Smean's published workspace description](https://blog.smean.ai/en/posts/introducing-smean-2/) informed the consistent workspace, spacing and cross-device approach. No Smean assets were used. DOMROV has its own navy/white identity, muted green accent, mark and navigation. Khmer font files are self-hosted under `react-client/public/fonts`, with their OFL license; no external font request is needed.

## Implementation and routes

1. Foundation: semantic palette/spacing/radius tokens, responsive navigation, focus treatment, skip link, reduced motion, Khmer type and print styles.
2. `/`: question entry, examples, three service entry cards and recent local checklists. `/chat?q=…` pre-fills the composer for explicit submission. No question is sent just by opening a link.
3. `/chat`: existing working chat, supported answer and evidence cards, article and original PDF access, provenance/review notices and a next-step route into procedures. Unsupported answers without citations are suppressed even if the API claims sufficient evidence. Clear removes the current conversation and draft; conversations remain in memory only and disappear when leaving the route/reloading. A stale response is removed when a new request starts.
4. `/procedures`, `/procedures/:id`: driving licence, business registration and civil registration **unreviewed UI fixtures**. Missing, stale and conflicting states are simulated examples, not findings about an official service. Every unknown office, fee, processing time, hours, eligibility, document requirement and verification date is explicitly unverified. General research checklists are distinguished from official application steps.
5. `/saved`: device-local checklists, progress, individual/all deletion, empty and storage error states. Procedure detail provides save, reuse and browser print/Save as PDF. No cloud identity, team account or government tracking is implied. No sensitive chat content is written to localStorage.
6. `/search` and `/articles/:documentId/:articleNumber`: preserved existing contracts, filters and routes; added labelled search input, search retry and consistent DOMROV shell. Citation review flags are not treated as proof of verification. Fixed an existing mock citation mapping bug that passed array indices as relevance scores.

## API mapping and proposed procedure schema

`src/services/apiClient.ts` and `src/types/index.ts` remain unchanged:

| Action | Existing request |
| --- | --- |
| Search | `POST /api/search`, existing query/mode/filters/page/pageSize body |
| Chat | `POST /api/chat`, existing message/conversation/filters body |
| Read article | `GET /api/articles/{documentId}/{articleNumber}` |
| Laws | `GET /api/laws`, existing query parameters |

`VITE_USE_MOCK` defaults to demo unless exactly `false`. A global badge and notice disclose mode across all routes; procedure fixtures stay labelled demo in live API mode. Set the API base URL and mock flag in `.env` and restart Vite to change modes. Public source access has no payment gate.

The proposal in `src/services/procedures.ts` intentionally has no network endpoint: id/title/description, nullable eligibility/documents/office/fee/hours/timeframe/lastVerified, source title/URL pairs and explicit evidenceStatus. Backend and research owners must agree this schema and add field-level evidence, source authority, review date/reviewer policy, conflicting evidence resolution and freshness rules before production procedure guidance. No schema agreement or reviewed service records are claimed by this implementation.

## Validation, 15 November 2026

- `npm run build` and `npm run lint` from `react-client`: passed. The repository's lint script is a TypeScript build/type check, not ESLint.
- Chromium/Playwright: seven routes at each of 360, 768 and 1440px; no horizontal overflow; Khmer web font loaded.
- Main journey: question from home → submit chat → supported fixture answer → inspect citation/PDF href → read article → procedure research checklist → save → reload → reuse → print → delete → reload. Passed.
- Browser print invoked and a printable A4 PDF generated. Browser-specific Save as PDF dialog was not automated.
- Empty and exact-article search; missing article; insufficient evidence; keyboard skip/focus; reduced motion; corrupted and denied localStorage: passed.
- Live fetch client with intercepted API responses: chat/search POST body and article GET path assertions; simulated network failures and retries on chat/search/article; answer-without-citations suppression; passed. This is contract testing, not validation against a running backend.
- No browser runtime errors in the demo suite. Visually inspected desktop/mobile home and answer screenshots; all route captures available under `docs/domrov-qa/`.
- Original PDF URLs are preserved and HTTP(S) links validated. Remote source availability and the correctness of existing legal fixtures were not verified. They remain marked demo.

Screenshots: [desktop home](domrov-qa/home-1440.png), [mobile home](domrov-qa/home-360.png), [tablet home](domrov-qa/home-768.png), [desktop answer](domrov-qa/answer-1440.png), [mobile answer](domrov-qa/answer-360.png), [procedure](domrov-qa/procedure-360.png), [print artifact](domrov-qa/checklist.pdf).

Reproduce using the repository Python environment with Playwright and Chromium installed:

```bash
npm run dev --prefix react-client -- --host 127.0.0.1
# In another terminal, from repository root:
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome .venv/bin/python react-client/scripts/domrov_qa.py
# API-contract suite: start a second Vite server with VITE_USE_MOCK=false, port 5174
VITE_USE_MOCK=false npm run dev --prefix react-client -- --host 127.0.0.1 --port 5174
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome .venv/bin/python react-client/scripts/domrov_api_qa.py
```

## Remaining dependencies

Reviewed pilot records for 2–3 services, confirmed procedure API/schema, authoritative source/verification metadata, and real backend integration acceptance. Cloud persistence/accounts/team permissions remain future work. Current answer and procedure sections are deliberately separate data boundaries within one product: the legal chat contract cannot supply verified administrative requirements. A Khmer-speaking content reviewer should review the interface copy before public release.
