# Khmer Law Plain-Text Extraction

Read the uploaded Khmer legal document chunk carefully and extract all available text in its original reading order.

Return only the extracted plain text. Do not return JSON, CSV, Markdown code fences, explanations, summaries, translations, or extraction metadata.

Rules:

1. Preserve the original Khmer text, spelling, punctuation, numbering, and symbols as accurately as possible.
2. Do not translate, summarize, rewrite, correct, or omit any text.
3. Preserve article headings such as មាត្រា១, មាត្រា ១, មាត្រាទី១, មាត្រាទី ១, and Article 1.
4. If a chunk starts with ordinary text without an article heading, preserve it exactly. Do not invent a heading.
5. If an article continues from an earlier page or chunk, preserve the continuation as part of the same article. Do not add a new heading.
6. Preserve meaningful paragraph breaks, but remove only unnecessary line breaks caused by PDF formatting.
7. Preserve all available text, including incomplete text at the beginning or end of this chunk.
8. The example labels below are instructions only, not document content. Never output labels such as Chunk 1 or Chunk 2 unless they actually appear in the document.

Example of consecutive chunks:

Chunk 1 — Article starts normally

មាត្រា១

ច្បាប់នេះមានគោលបំណងកំណត់អំពីសិទ្ធិ និងកាតព្វកិច្ចរបស់បុគ្គល។

មាត្រា២

បុគ្គលគ្រប់រូបត្រូវគោរពតាមបទប្បញ្ញត្តិនៃច្បាប់នេះ។

Chunk 2 — Continuation without article heading

ការអនុវត្តសិទ្ធិទាំងនេះត្រូវធ្វើឡើងដោយគោរពតាមច្បាប់ជាធរមាន។

មាត្រា៣

បុគ្គលគ្រប់រូបមានសិទ្ធិទទួលបានការការពារតាមច្បាប់។

When processing Chunk 2, the text before មាត្រា៣ remains part of មាត្រា២. Do not add a new heading to that continuation. The example labels and example text are instructions only, not document content.

Output only the extracted text from the uploaded document chunk.
