## Plan: Improve Retrieval Accuracy & Speed

TL;DR
Use Retrieval-Augmented Generation (RAG) with a hybrid retriever (lexical + semantic), a fast local vector index (FAISS) or cloud vector DB, and strict low-temperature Groq prompting. Add an evaluation harness, logging, and a human correction loop. Prioritize retrieval speed (fast index + caching) and answer precision (source-labelled context + strict LLM instructions).

**Steps**
1. Implement lightweight RAG pipeline (short-term, *blocks: none*):
   - Add a context assembler that collects top-k matching rows from current CSV retrievers, tags each block with a SOURCE label (e.g., "SOURCE: facilities.csv"), clamps context size, and returns the context string. (Already added in `backend/calls/views.py`.)
   - Use `_groq_answer_from_context(question, context, data_source)` with temperature 0–0.2 and short max tokens.

2. Add semantic indexing + hybrid retrieval (*depends on step 1*)
   - Create embeddings for each CSV row (use sentence-transformers locally or cloud embeddings).
   - Index embeddings in FAISS (local) or a managed vector DB (Pinecone/Weaviate/Milvus/Chroma).
   - At query time run both: lexical search (existing retrievers) + semantic top-N (vector), merge results de-duplicated and rank by recency/relevance.

3. Optimize retrieval for speed and relevance (*parallelizable with step 2*)
   - Precompute embeddings offline and store row→metadata mapping.
   - Use compact embedding model for speed (e.g., all-MiniLM), quantize FAISS index for memory/speed.
   - Cache recent query→results and warm-start for common queries.
   - Limit top_k (start with 8) and context char/token budget (e.g., 3500 chars).

4. Prompt engineering & safety rules (*depends on step 1*)
   - Use a short system/user prompt that enforces: "Answer ONLY from provided context; if not present say it's unavailable; be concise (1–2 sentences); append short source tag."
   - Force low temperature and deterministic decoding where possible.

5. Monitoring, evaluation & feedback loop (*parallel*)
   - Build evaluation harness: a CSV of test queries → expected answer + source. Measure precision@1, source-correctness, and latency.
   - Log retrieval candidates, final model answer, and whether the cited source contains the answer.
   - Add a simple UI or API flag to mark an answer as incorrect; collect corrected Q→A pairs.

6. Iteration & next steps
   - Tune retrieval top_k, context truncation, and prompt templates from evaluation metrics.
   - If accuracy still low and you have hundreds+ labeled examples, consider supervised fine-tuning or retrieval-augmented instruction-tuning.

**Relevant files / components (what to change or add)**
- backend/services/data_retriever.py — keep and stabilize CSV parsing and lexical search.
- backend/calls/views.py — use and refine `_assemble_local_context()` and `_groq_answer_from_context()` (already in place).
- Add: services/vector_index.py (index + query wrapper), scripts/build_embeddings.py (one-time indexer), tests/eval/run_eval.py (evaluation harness).
- gencall_backend/settings.py — add vector DB / embedding settings and indexes paths.

**Verification**
1. Unit tests: retrieval functions return expected rows for 50 curated queries.
2. Evaluation: run test set → target metrics: precision@1 ≥ 0.85, source-correctness ≥ 0.9, average retrieval + LLM latency < 800ms (local FAISS) or <1200ms (managed DB).
3. Manual spot-check: 30 random user queries via frontend show concise answers and correct source tags.

**Decisions & assumptions**
- Default approach: FAISS + sentence-transformers for local dev (fast, cheap). Option to switch to managed vector DB later.
- Use Groq for final answer generation; embeddings can be from local model or cloud depending on privacy/cost.
- Keep structured heuristics (keyword intent) to route obvious queries to deterministic retrievers.

**Further Considerations (short)**
1. CSV updates: implement incremental re-indexing on file change.
2. Cost & privacy: if CSVs contain PII, prefer local indices and local embedding models.
3. Tune top-k and context size; smaller context often improves precision.


If you approve, I can start with one of these immediate actions:
- A) Add FAISS + embedding pipeline and wire it into the existing Groq flow.
- B) Build the evaluation harness and run an initial test set.
- C) Tighten prompts and test with sample queries (fastest).

Respond with A / B / C and I will start implementing and updating the plan file accordingly.
