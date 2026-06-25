# Product Roadmap — 3GPP RAG Assistant

Milestones are defined by the outcome they unlock, the metric that confirms them, and the architectural decision each one either closes or defers. This is not a sprint calendar — phases are complete when their success criteria are met, not when a date arrives.

---

## Completed milestones

### M1: Working RAG over a single spec
**Outcome:** An engineer can ask a natural-language question about one 3GPP spec and get a cited, grounded answer.  
**Success criteria met:** End-to-end pipeline functional (retrieve → prompt → generate); answer includes source citation; multi-turn conversation works; CLI and Streamlit UI available.  
**Key decisions closed:** RAG over fine-tuning (ADR-001); bge-small embedding choice (ADR-003); chunk size 1000/200 (ADR-004).  
**What it proved:** The chunking + retrieval pipeline works for dense technical text. Semantic search surfaces relevant clauses that keyword search misses.

---

### M2: Production-ready multi-spec coverage
**Outcome:** The same engineer can query across 37 specs spanning 5G NR, LTE, and Core — and filter by domain or generation — without touching config files.  
**Success criteria met:** 44,290 chunks indexed from 37 specs; domain/generation filtering in UI and API; dedup-to-latest-version indexing prevents conflicting results across releases; `/catalog` endpoint shows indexed status per spec.  
**Key decisions closed:** Dedup to latest version (ADR-007); metadata-driven filtering via ChromaDB `where` clauses.  
**What it proved:** The indexing and retrieval architecture scales to a real corpus without degrading query quality.

---

### M3: Public deploy, cloud path, security hardening
**Outcome:** Anyone with a browser can use the assistant without installing anything, and the app is safe to expose publicly.  
**Success criteria met:** Live Streamlit Cloud app running Groq llama-3.3-70b; pre-built vectordb distributed via GitHub Release asset; 42 vulnerabilities from formal security audit resolved across two hardening rounds [source: owner's audit notes]; rate limiting, SSRF prevention, path-traversal protection, prompt injection defence, security headers, input bounds all in code.  
**Key decisions closed:** Dual-provider LLM architecture (ADR-002); ChromaDB ONNX on cloud (ADR-005); security-before-public-launch (ADR-006).  
**What it proved:** A side project can ship with production-grade security posture. Most personal AI tools skip this entirely; this one didn't.

---

## In progress

### M4: Eval rigor — retrieval + answer quality
**Outcome:** Any reviewer can reproduce the eval in one command and trust the numbers.  
**Success criteria:**
- Recall@k, MRR, nDCG@k, and hit-rate added to the retrieval harness alongside the existing precision/recall heuristics
- A versioned golden dataset (`data/eval/golden_set.jsonl`) with ground-truth sources and expected facts — real and checkable against the corpus
- LLM-judge faithfulness and answer-correctness path (configurable Groq or Ollama judge)
- `--regression` mode: non-zero exit if any metric falls below the stored baseline
- `EVAL_REPORT.md` documenting methodology, limitations, current numbers (2026-02-27), and `[RUN REQUIRED]` placeholders for what needs the full index + LLM

**Metric that confirms it:** Retrieval pass rate and Recall@5 reproducible with a single command; LLM-judge faithfulness run and published.  
**Status:** Harness expansion and golden dataset are under active development (Stream B). LLM-judge results require a run on the live index — marked `[RUN REQUIRED]` until Eric runs it.

---

### M5: Corpus-agnostic architecture
**Outcome:** A developer can point this system at any technical or regulated document corpus by swapping a config — not by forking the codebase.  
**Success criteria:**
- A documented seam for corpus configuration (loader interface or `CorpusConfig` dataclass) so 3GPP-specific logic is isolated and swappable
- `GENERALIZE.md` with a worked example: how to replace the 3GPP catalog and cleaner with a different corpus
- All 160 existing tests still pass; 3GPP remains the default and only implemented corpus
- No fabricated "supports X corpora" claims — framed honestly as "designed to generalize; 3GPP is the implemented corpus"

**Metric that confirms it:** A reader can trace in code exactly where the 3GPP-specific parts plug in; no behavior change on the 3GPP path.  
**Status:** Under active development (Stream D).

---

## Planned

### M6: Multi-document reasoning across spec boundaries
**Outcome:** A question that spans two or more specs (e.g., "How does the F1 interface interact with the NGAP protocol?") gets a single coherent answer that correctly integrates content from TS 38.473 and TS 38.413, rather than two disconnected responses.  
**Why it's hard:** Current retrieval returns top-k chunks without regard for cross-spec dependencies. Multi-hop reasoning requires either a re-ranking step that promotes cross-spec coverage, or an agentic loop that issues sub-queries per spec and merges answers.  
**Decision to make:** Re-ranker vs agentic retrieval vs query decomposition. All three are architecturally viable; the choice depends on latency tolerance and whether the user can see intermediate reasoning steps (which changes the UX model).  
**Success criteria:** Pass rate on a cross-spec golden set ≥ single-spec pass rate; no regression on single-spec queries.

---

### M7: Hosted team version with auth and shared sessions
**Outcome:** A telecom team (e.g., an RAN engineering group) can use the assistant as a shared tool — with login, per-user session history, and an admin view — rather than as a public anonymous app.  
**Why it matters:** The current public app has no user context. A team version enables usage analytics (which specs are queried most?), per-engineer session continuity, and access control for sensitive configurations.  
**Decision to make:** Auth provider (OAuth via GitHub/Google vs enterprise SSO); session storage (in-process dict vs Redis); hosting (Streamlit Cloud doesn't support server-side auth well — likely moves to a container deploy).  
**Success criteria:** Authenticated users can persist session history across logins; admin can see aggregate query patterns; rate limiting migrates from in-process (current) to distributed.

---

### M8: Eval-gated CI and regression prevention
**Outcome:** A pull request that degrades retrieval quality fails CI before it merges.  
**Why it matters:** Currently the eval harness is a manual script. As the codebase evolves, a chunking change or a config update could silently degrade retrieval pass rate. The `--regression` mode (planned in M4) is the foundation; this milestone wires it into `.github/workflows/ci.yml`.  
**Decision to make:** Which metrics gate the build (pass rate only? recall@5? faithfulness?); what the regression threshold is; whether the eval runs on a small fast subset or the full 44K-chunk index (runtime cost in CI).  
**Success criteria:** CI fails on a deliberate regression (test); eval result is committed to the repo after each run so the baseline stays current.

---

## What this roadmap does not include

- User counts, adoption numbers, or revenue. This is an open-source personal project. Usage metrics are not the measure of success for this tool — eval quality, security posture, and architectural clarity are.
- A "launch date." Milestones ship when their success criteria are met.
- Features without a defined success metric. If it can't be measured, it belongs in a speculative backlog, not a roadmap.

---

## README embed block

The following condensed block is provided for Stream A to embed in README.md:

```markdown
## Roadmap

Milestones are defined by outcome and success criteria, not sprint dates.

| Milestone | Status | Success criteria |
|---|---|---|
| M1: Working RAG over a single spec | Complete | End-to-end pipeline; cited answers; multi-turn UI |
| M2: Multi-spec coverage (37 specs, domain/generation filtering) | Complete | 44,290 chunks indexed; metadata filtering in UI + API |
| M3: Public deploy, dual LLM path, security hardening | Complete | Live Streamlit Cloud app; 42 vulnerabilities resolved |
| M4: Eval rigor (Recall@k, MRR, nDCG, LLM-judge) | In progress | Reproducible one-command harness; golden dataset; regression mode |
| M5: Corpus-agnostic architecture | In progress | Documented seam in code; GENERALIZE.md; all 160 tests pass |
| M6: Multi-document reasoning across spec boundaries | Planned | Cross-spec golden set pass rate ≥ single-spec baseline |
| M7: Hosted team version with auth + shared sessions | Planned | Auth, per-user history, distributed rate limiting |
| M8: Eval-gated CI | Planned | Regression in retrieval quality fails CI automatically |

Full milestone details: [`docs/portfolio-upgrade/ROADMAP.md`](docs/portfolio-upgrade/ROADMAP.md)
```
