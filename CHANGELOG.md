## 2026-11-13

- [WS-DEPENDENCIES-001] Repaired local WebSocket dependency composition and deterministic text analysis.
- Test: dependency module compilation and local orchestrator composition passed.
- Test: direct WebSocket simulation passed after adding `httpx2` to the backend requirements.

- [VISUAL-DB-001] Added database-backed image selection, image retrieval, and visual delivery messaging.
- Test: `python -m unittest discover -s backend/tests -p "test_image_pipeline.py"` passed.
- [STORAGE-001] Connected PostgreSQL image catalog and S3-compatible storage through environment configuration.
- Test: PostgreSQL configuration and S3 adapter checks passed without exposing credentials.
- [STORAGE-002] Added an idempotent PostgreSQL migration and a safe `.env.example` template.
- [STORAGE-003] Accepted the configured `AWS_ENDPOINT_URL_S3` variable for the complete visual pipeline.
- [STORAGE-004] Full pipeline test stopped after the database/S3 stage timed out; analysis and task queue stages passed.
- [STORAGE-005] Removed PostgreSQL image catalog access and switched image discovery to direct object storage listing.
- [STORAGE-006] Aligned object storage image discovery with bucket `assets` and prefix `uploads/`.
- [DOCS-001] Documented concise final-only communication and prohibition of displayed internal reasoning in AGENTS.md.
- [STORAGE-007] Full pipeline test reached object storage but stopped because no matching image was returned.
- [STORAGE-008] Logged the full pipeline test and stopped before image delivery because vector search is not implemented.
- [VECTOR-001] Downloaded EmbeddingGemma through Ollama; vector search needs text metadata because the model embeds text, not image pixels.
- [VECTOR-002] Added Ollama image captioning, EmbeddingGemma vectors, cosine ranking, and a cached S3 vector index.
- Test: visual pipeline and vector-index unit tests passed; Ollama embedding and vision API smoke tests passed.
- [VECTOR-003] Documented caption-based vector indexing and cached S3 index behavior.
- Test: `python -m unittest discover -s backend/tests -p "test_image_pipeline.py"` passed; local Ollama returned 768-dimensional text vectors and an image caption.
- [VECTOR-004] Full pipeline test passed analysis and object-store vector search, but stopped because the bucket contained no indexed images.
- [VECTOR-005] Wired LLM 2 to Ollama Qwen 2.5 1.5B and corrected S3 prefix after discovering images in the bucket root.
- [VECTOR-005] Retested using bucket `hackathon` and prefix `uploads/`; vector search found zero images, so no visual result was emitted.

## 2026-11-12

- [NEON-REMOVAL-001] Removed Neon PostgreSQL and Neon S3 startup dependencies and exposed the WebSocket router through the HTTP application.
- Test: WebSocket simulation stopped because no orchestrator is configured in the application.
