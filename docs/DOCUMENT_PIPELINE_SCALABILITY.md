# Document Pipeline Scalability — AcademicCheck AI

Date: 2026-09-09  
Code: `backend/app/services/documents/extractor.py`, `validation.py`, upload chunking in `documents.py`.  
Artifact: `ops/cert_document_extract.json` 2026-09-09T20:46:20Z (`.txt` only, after one warmup extract).

## Audit

| Stage | Behavior | Parallelism | Memory |
| --- | --- | --- | --- |
| Upload | 1 MiB async chunks; cap `max_upload_mb=15` | Single request | Buffer then join |
| Validation | Magic bytes, PDF JS reject, size | Sync | Full bytes |
| PDF parse | `_extract_pdf` page loop | Sync; **not benched** | Full extracted string |
| DOCX parse | `_extract_docx` | Sync; **not benched** | Full extracted string |
| Normalization | `_normalize` + paragraph split | Sync | Second copy (`text` + `normalized_text`) |
| Analysis prep | Heuristic `run_analysis` on extracted text | RQ job (one doc / job) | Cap `max_extracted_chars=400000` |
| Caching | None at extract layer | — | — |

Safety fail-closed if extracted text exceeds 400k characters. First process extract paid **~8.7 s** (langdetect import) before warmup; that cold start is a real latency cliff, not in the timed table.

## Benchmarks (`.txt`, tracemalloc)

| Size class | Chars | Words | Latency ms | Peak traced bytes | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Small | 1,048 | 136 | **285.1** | 131,656 | Timed |
| Medium | 10,480 | 1,360 | **501.4** | 598,831 | Timed |
| Large | 52,400 | 6,800 | **814.5** | 1,296,271 | Timed |
| Very large | 157,200 | 20,400 | **1416.4** | 3,758,999 | Timed (under 400k cap) |
| PDF pages / large DOCX / parallel parse | — | — | — | — | **Not run** |

Throughput on this host for very-large `.txt`: about **42 docs/min** if serialized on one CPU and if this latency held — **not** a multi-worker upload test.

## Optimize vs this pass

No PDF thread pool (PyMuPDF page loop is request-local; thread safety not proven). Memory still holds full normalized text. Chunking is structural, not map-reduce LLM.

## Verdict

Pipeline is **bounded** (15 MB / 400k chars) and **timed for `.txt` tiers**. It is **not** certified for PDF/DOCX parse throughput or RSS at the upload cap. Do not claim parallel document parsing.
