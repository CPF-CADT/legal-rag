# Khmer Law Plain-Text Extraction

Read the uploaded Khmer legal document chunk carefully and extract all visible text in its original reading order.

Return only the extracted plain text with article markers. Do not return JSON, CSV, Markdown code fences, explanations, summaries, translations, or extraction metadata.

## Rules

1. Preserve the original Khmer text, spelling, punctuation, numbering, and symbols as accurately as possible.
2. Do not translate, summarize, rewrite, correct, invent, or omit readable text.
3. Detect actual article headings such as `មាត្រា១`, `មាត្រា ១`, `មាត្រាទី១`, `មាត្រាទី ១`, and `Article 1`.
4. Before every actual article heading, output `[START_ARTICLE:N]` on its own line, where `N` is the article number converted to Arabic digits (e.g., `១` → `1`, `១២` → `12`). Do not renumber articles sequentially.
5. Keep the original article heading on its own line immediately after the marker. Preserve its original numbering, spacing, punctuation, and wording.
6. Do not output `[START_ARTICLE:N]` for references to articles inside paragraphs, tables, or other ordinary text.
7. If a chunk starts with text continuing from a previous article, preserve it without adding a new article heading or marker.
8. If an article continues beyond the current chunk, preserve all visible text without adding an ending marker.
9. Preserve meaningful paragraph breaks, but remove unnecessary line breaks caused by PDF formatting.
10. Preserve all readable text, including chapter headings, section headings, ordinary text, and incomplete text at chunk boundaries.
11. Do not reconstruct missing or unreadable text based on legal context. Extract only text that can be reliably identified.
12. Do not add page numbers, chunk numbers, separators, metadata, or markers other than `[START_ARTICLE:N]`. Preserve page numbers only when they are part of the actual legal content.
13. Never invent, repeat, move, or renumber article headings.
14. The examples below illustrate the output format only. Never copy example text or labels into the actual extraction.

## Example of Consecutive Chunks

**Chunk 1 — Article starts normally**

[START_ARTICLE:1]

មាត្រា១

ច្បាប់នេះមានគោលបំណងកំណត់អំពីសិទ្ធិ និងកាតព្វកិច្ចរបស់បុគ្គល។

[START_ARTICLE:2]

មាត្រា២

បុគ្គលគ្រប់រូបត្រូវគោរពតាមបទប្បញ្ញត្តិនៃច្បាប់នេះ។

**Chunk 2 — Continuation without article heading**

ការអនុវត្តសិទ្ធិទាំងនេះត្រូវធ្វើឡើងដោយគោរពតាមច្បាប់ជាធរមាន។

[START_ARTICLE:3]

មាត្រា៣

បុគ្គលគ្រប់រូបមានសិទ្ធិទទួលបានការការពារតាមច្បាប់។

## Important Instructions

- Text appearing before the first article marker in a chunk may be a continuation of an article from the previous chunk.
- Never add a marker to continuation text unless a new article heading actually appears.
- An article ends when the next actual article begins, or when the downstream parser determines its boundary from document structure.
- Preserve the original article heading even though its number is already included in the marker.
- The example chunk labels, Markdown formatting, and example content are instructions only, not output.

## Final Output

Return only the extracted document text with `[START_ARTICLE:N]` markers. Do not include anything else.
