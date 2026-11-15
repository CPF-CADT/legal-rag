# DOMROV frontend implementation task

## Goal
Build a polished Khmer-first DOMROV frontend inspired by Smean's clear workspace structure, responsive layout and easy onboarding. Present legal intelligence and public-service guidance as one product. Use an original DOMROV identity, not copied Smean assets.

Status: Ready for planning. Priority: High. Owner: Unassigned.
This issue defines future implementation; no frontend changes have been made by this review.

## Existing frontend audit
Reviewed default branch main on 15 November 2026 (source review, not a live visual or runtime test).
- apps/react-client: React 18, TypeScript, Vite 5, Tailwind 3, React Router 6.
- src/routes/AppRoutes.tsx maps / and /chat to ChatPage; HomePage exists but is not routed.
- ChatPage already composes sidebar, greeting, messages, composer and citations; reuse these.
- CitationDrawer shows source title, article and original PDF; extend it with provenance and verification status.
- useChatSessions persists conversations in localStorage; this is device-local history, not authenticated cloud/team storage.
- src/services/api.ts defaults to mockApiClient unless VITE_USE_MOCK=false.
- globals.css uses Noto Sans Khmer; variables.css contains only --legal-blue. Build a consistent token system.
- User-facing legacy LegalRAG/ធីតា naming appears in reviewed pages; align visible product copy with DOMROV.

## Work breakdown
- [ ] FE01 Design foundation: original deep navy/white palette, restrained accent, Khmer/English type scale, 8px spacing system, buttons, cards, inputs, focus states and responsive navigation.
- [ ] FE02 Home/workspace: prominent question input, example questions, service entry cards and recent work. Decide / home and /chat workspace routing while preserving search/article deep links.
- [ ] FE03 Answer experience: short explanation, legal basis, eligibility, documents, numbered steps, office/channel, published fees/hours/timeframes, sources and last-verified information.
- [ ] FE04 Procedure catalog/detail: support 2–3 reviewed services; model missing, stale and conflicting evidence explicitly. Use clearly labelled fixtures until service APIs exist.
- [ ] FE05 Saved work: reusable checklist and print/export; explain device-local persistence and provide clear/delete controls. Cloud accounts/team permissions remain a later dependency.
- [ ] FE06 API integration: preserve existing legal search/chat contracts; agree procedure schema with backend; show demo status, loading, empty, unavailable, insufficient-evidence and retry states.
- [ ] FE07 QA: keyboard/focus, Khmer glyphs and long text, 360/768/1440px layouts, source links, navigation, network errors, persistence, and production build.

## Acceptance criteria
- [ ] One coherent DOMROV experience covers legal explanation plus service steps.
- [ ] Main journey works: question → supported answer → source inspection → checklist → print/save.
- [ ] No fabricated offices, fees, dates, verification badges or completion guarantees; missing values say not verified.
- [ ] Mock mode is visibly identified; it cannot be presented as verified live guidance.
- [ ] No horizontal overflow at target widths; readable Khmer, labelled controls, visible keyboard focus, adequate contrast and reduced-motion support.
- [ ] Existing legal chat/search/article links still work with the supported API.
- [ ] npm run build and npm run lint pass; record manual checks and screenshots for implemented screens.
- [ ] Sensitive conversation persistence is disclosed and user-controllable.
- [ ] Public source access and evidence quality do not depend on payment.

## Design and business boundaries
Smean reference: https://www.smean.ai/home/ and https://blog.smean.ai/en/posts/introducing-smean-2/
Reference review covered homepage content and published design descriptions; screenshot inspection was unavailable.
Use task-focused workspace patterns, generous spacing and subtle motion. Keep sources prominent.
Do not add payments, subscriptions, fake team accounts, real-time government application tracking or referral rewards in this first task.
Future pricing hypotheses: Pro $3–$5/month; team $20–$50/month; organizational setup/maintenance scoped separately. Validate before implementation.

## Dependencies and delivery order
Design system → home/chat shell → evidence/procedure components → API and saved checklist → QA.
Backend owner must confirm source/verification fields and procedure endpoints; research reviewer supplies pilot records.
Deliver design tokens, implemented routes/components, API mapping, QA evidence and a short handover.

