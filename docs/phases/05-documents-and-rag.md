# Phase 05 — Documents and RAG

## Objective
Create a provenance-preserving bilingual document store and local pgvector retrieval pipeline for EGX reports, statements, disclosures, announcements, and news. Retrieval must provide auditable evidence—not answers—and must retain source, publication date, page/section, company, language, and temporal eligibility.

## Prerequisites
- Phases 00–04 accepted; pgvector works, stock identity is stable, and source/timestamp safety rules are established.
- Ollama embedding model `qwen3-embedding:4b-q4_K_M` is installed for real local integration, but deterministic fake embeddings are available for tests.
- Legal public-source collection policy is documented: terms/robots/access limits, copyright/storage constraints, URL and publication-date validation, and no bypass of access controls.
- Supported initial inputs and extraction tools are selected (text PDF/HTML first; OCR and complex tables may be explicitly deferred).

## Expected modules and artifacts
- Document/chunk persistence models, migrations, Pydantic schemas, source adapters/manual importer, raw-file storage convention, checksum/version handling.
- `backend/app/rag/`: extraction, cleaning, language detection/validation, structure-aware chunking, embedding provider abstraction, indexing, filtered retrieval, citation assembly.
- Local Ollama embedding adapter plus deterministic `FakeEmbeddingProvider`; ingestion/retrieval APIs or local commands.
- Arabic/English and mixed-language fixtures, table fixtures, golden retrieval dataset, source-validation record, and tests.

## Schema/API changes
`documents`: `id`, nullable stock reference/`symbol`, `document_type` (`ANNUAL_REPORT`, `QUARTERLY_REPORT`, `FINANCIAL_STATEMENT`, `DISCLOSURE`, `COMPANY_ANNOUNCEMENT`, `NEWS`), `title`, `language`, normalized `content`, raw file/path reference where allowed, MIME type, checksum, `source`, `source_url`, `published_at`, `fetched_at`, `created_at`, version/status, extraction metadata. Never silently replace an older document/version.

Add `document_chunks`: `id`, `document_id`, stable ordinal, `content`, `language`, token count, page start/end, section/table metadata, checksum, `embedding vector(dimension)`, embedding model/version/dimension, `created_at`; unique document-version/ordinal/checksum and vector plus metadata indexes. Dimension must exactly match the pinned model and migration choice.

Contracts may include document list/detail/import/status and `POST /api/documents/search` with `query`, optional `symbol`, types, language, `published_before/as_of`, date range, and `top_k`. Results include chunk text, score with documented semantics, document/title/source URL/publication date, page/section, language, and model/index version. Raw local paths are never exposed as public URLs.

## Ordered tasks
1. Define canonical metadata, source allowlist/review process, raw retention/versioning, duplicate policy, temporal rules, and safe file-size/type limits.
2. Add document and chunk migrations with pgvector indexes appropriate to the small local corpus. Record exact embedding dimension from an actual model probe before fixing schema.
3. Implement idempotent ingestion: acquire permitted source/manual file, hash bytes, validate metadata, preserve raw input, extract text and page/section structure, clean conservatively, and persist atomically.
4. Handle UTF-8 Arabic/English, right-to-left characters, Arabic/Western digits, and mixed documents without destructive normalization. Retain original text alongside search normalization if used.
5. Implement structure-aware chunking targeting 800–1200 tokens and 100–200 overlap. Keep headings with content; treat tables as atomic structured blocks or defer them with explicit warnings—never blindly split rows.
6. Add embedding abstraction, deterministic fake, and Ollama adapter with batching, bounded timeouts, model/dimension validation, and resumable indexing. Version embeddings; model changes require re-indexing, not mixed-vector search.
7. Implement query embedding, metadata pre-filtering (especially symbol and publication cutoff), vector search, deterministic tie-break, deduplication/diversification, and citation construction.
8. Create bilingual golden queries and expected relevant chunks; tune only against fixed evaluation data and record parameters.
9. Add ingestion/re-index/status/search contracts and operational recovery documentation.

## Algorithms and edge cases
- Identity uses content checksum plus source/version metadata. Same bytes from multiple URLs may retain aliases; changed bytes create a new version. Never mutate publication date to retrieval date.
- Publication date must be validated from the original page/document; unknown remains unknown and is ineligible for strict historical `as_of` unless explicitly allowed with warning.
- Token counts must use the selected embedding tokenizer or a documented approximation. Oversized tables/pages use table-aware segmentation with repeated headers and page citations; scanned/image PDFs return `OCR_REQUIRED`, not empty success.
- Normalize whitespace/hyphenation conservatively. Do not strip Arabic diacritics, punctuation, digits, or RTL marks from preserved content; a separate search-normalized field may be used and tested.
- Reject password-protected, executable, unsupported MIME, zip-bomb-like, oversized, corrupt, or path-traversal inputs safely. Treat document content as untrusted data, never instructions.
- Retrieval applies filters before ranking where possible. Exact score is model/index-specific and not confidence/probability. Equal scores use stable document/chunk order. Avoid returning many overlapping chunks from one page.
- Empty query, unknown symbol, no eligible documents, embedding outage/dimension mismatch, interrupted indexing, deleted/replaced source, duplicated chunks, and multilingual query/document mismatch produce explicit states.
- `as_of` excludes documents published after cutoff, preventing look-ahead. Source URL, date, and page/section survive every transformation.

## Tests
- Unit tests for metadata validation, checksum/versioning, Arabic/English cleaning, token windows/overlap, heading/table/page preservation, citation formatting, and temporal filters.
- Migration/integration tests for pgvector dimension/index, idempotent ingestion, new versions, rollback after extraction/embedding failure, resumable re-index, and stable ranking ties.
- Retrieval evaluation with fixed Arabic, English, and mixed queries; assert relevant source/chunk, correct company/date filters, no post-`as_of` leakage, and citation completeness—not exact natural-language answers.
- Security tests for malformed/oversized/unsupported files, traversal filenames, prompt-injection text, unsafe URLs, and raw path leakage.
- Fake embeddings make the default suite offline and deterministic. Ollama embedding and approved public-source tests are explicit local opt-in tests.

## Manual demo
1. Import one English and one Arabic permitted COMI disclosure/report; show raw checksum, source URL, publication date, language, pages, and version.
2. Show chunks near the target size with overlap, headings, and a preserved/table-warning example.
3. Index with local Qwen embeddings and search “What caused the decline in net income?” and its Arabic equivalent with COMI/date filters.
4. Display ranked evidence with title, source, publication date, page/section, language, and score; open the original source and verify the excerpt.
5. Apply an earlier `as_of` cutoff and prove later documents disappear. Re-import identical bytes (no duplicate) then changed bytes (new version).
6. Stop Ollama during indexing and demonstrate recoverable pending status without losing the document.

## Observability and failure handling
- Correlated structured events cover source/document/version/checksum prefix, extraction status/pages/chars, chunk count/token range, embedding model/dimension/batch latency, index status, query filters/result count, and safe error codes.
- Do not log entire copyrighted documents, private local paths, portfolio context, or query content by default; allow local debug only with explicit warning/redaction.
- Per-document states (`pending`, `processing`, `indexed`, `failed`, `superseded`) and stage-specific errors support retries. Atomic stages preserve the last valid index; dimension/model mismatch fails closed.
- Retrieval responses clearly report no evidence, incomplete indexing, unavailable embedding service, and unknown dates instead of fabricating context.

## Acceptance checklist
- [ ] Document and chunk models preserve raw/source/version/date/language/page lineage.
- [ ] Public-source usage and representative documents are manually validated.
- [ ] Arabic/English text and citations round-trip without destructive normalization.
- [ ] Chunking meets targets and handles tables explicitly rather than blindly.
- [ ] Embeddings are local, versioned, dimension-checked, and replaceable by a fake in tests.
- [ ] Search filters company/date/type/language and excludes future publications for `as_of`.
- [ ] Every result has complete evidence metadata; score is not called confidence.
- [ ] Ingestion is idempotent/resumable and failures do not destroy valid versions.
- [ ] Offline deterministic tests and bilingual retrieval evaluation pass.
- [ ] This phase supplies evidence only; it does not generate investment advice.

## Dependencies
- Upstream: phase 00 (PostgreSQL/pgvector/Ollama environment), phase 01 (stock identity); source conventions align with phases 02–03. Phase 04 is sequence-complete but not technically required.
- Downstream: phase 06 uses document search as a tool and provides answer generation.
- External public sites are optional at runtime; retained permitted documents and mocks support local development.
