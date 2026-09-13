# Requirements Traceability Matrix — AcademicCheck AI

Date: 2026-09-07 (Pass 3)  
Source of truth: original product specification (sections 1–108), 6 Sep 2026.  
Rule: PASS only with code **and** test or shipped UI/API evidence. Unrun production drills are not PASS. Scores are not increased without artifacts.

Pass 3 (Bucket A): CSRF/webhook security metrics; Flutterwave/Paystack UUID PK fix; Stripe/FLW webhook HTTP tests; ledger mismatch; DLQ+SIGTERM tests; jobs metrics; migration 008; compose pool alignment; A-PAY alert spec; settings focus trap; rollback script; coverage remeasure **80.98%**. See `docs/PASS3_EVIDENCE_INDEX.md`. FAIL IDs unchanged.

---

## REQ-1 Product vision / workflow
**Classification:** PARTIAL  
**Implementation:** Assignment → question → level → style → analysis → report → recheck exists. Compare drafts exists if two versions analysed.  
**Evidence:** `frontend/app/check/page.tsx`; `test_api_workflow.py`; versions UI.  
**Risk:** Spec “revise → Draft 2 → compare → submit” is not an automated E2E; submit-to-LMS does not exist (correct for MVP).

## REQ-2 Academic integrity position
**Classification:** PASS  
**Implementation:** No essay generator. Prompts forbid invented sources/quotes/stats/page numbers. Disclaimers on report/PDF/landing.  
**Evidence:** `provider.py` SYSTEM_PROMPT; `hallucination.py`; `test_prompt_injection.py`; `test_ai_heldout.py`; report disclaimer in `test_api_workflow.py`.  
**Risk:** Heuristic suggestions could still be misused as rewrite fodder; product copy forbids full rewrite.

## REQ-3 Target users
**Classification:** PARTIAL  
**Implementation:** Academic levels high_school→researcher; roles guest/student/tutor/admin/institution.  
**Evidence:** `check/page.tsx`; `seed.py` roles; isolation tests.  
**Risk:** Tutor/lecturer/writing-centre products are not distinct apps.

## REQ-4 Global market
**Classification:** PARTIAL  
**Implementation:** English UI; display currencies; Ghana/Nigeria/Kenya SEO pages.  
**Evidence:** `billing.py` DISPLAY_RATES; `seed.py` country slugs.  
**Risk:** Not a localized product for the full country list.

## REQ-5 Core product modules
**Classification:** PASS (modules exist as one engine)  
**Evidence:** `engine.py` `run_analysis`; `test_analysis_engine.py`.

### REQ-5.1 Essay Checker
**Classification:** PASS  
**Evidence:** Endpoint `POST /api/analysis`; UI `/check` and assignment check; report categories; `test_api_workflow.py`; `test_analysis_engine.py`.

### REQ-5.2 Assignment Checker
**Classification:** PASS  
**Evidence:** Question, level, citation style, word-count entitlements, optional rubric; `assert_can_analyze`; assignment workspace.

### REQ-5.3 Assignment Question Analyzer
**Classification:** PASS  
**Evidence:** `question.py` `analyze_question`; `test_question.py`; stored on assignment create; disclaimer not “exactly what lecturer wants” in copy.

## REQ-6 Assignment relevance check
**Classification:** PASS  
**Evidence:** `_relevance` in `engine.py`; eval relevance metrics; diagnostic not grade.

## REQ-7 Thesis checker
**Classification:** PASS  
**Evidence:** `classifiers.py` `classify_thesis`; `test_missing_thesis_is_flagged`; suggestions not auto-replace.

## REQ-8 Argument analyzer
**Classification:** PARTIAL  
**Evidence:** Claims/evidence/counterargument heuristics in `engine.py` / `classifiers.py`.  
**Risk:** Full CLAIM→EVIDENCE→ANALYSIS→CONCLUSION map is simplified vs spec diagram.

## REQ-9 Evidence analyzer
**Classification:** PASS  
**Evidence:** Supported / needs citation / potentially unsupported / cannot determine in `classifiers.py`; tests for cited vs uncited.

## REQ-10 Paragraph analyzer
**Classification:** PARTIAL  
**Evidence:** `_paragraphs` findings with paragraph numbers.  
**Risk:** Not every paragraph always scored “Strength: Moderate” in the spec’s exact card format; no dedicated pytest for paragraph 7 example.

## REQ-11 Structure analyzer
**Classification:** PASS  
**Evidence:** `structure_map` on report; UI table; a11y table test.

## REQ-12 Introduction checker
**Classification:** PASS  
**Evidence:** `_introduction` in `engine.py`; `test_introduction_conclusion_and_coherence_findings`; `test_missing_introduction_is_flagged` (`ops/cert_pass2_pytest.txt`).  
**Risk:** Heuristic detection only; not a pedagogy-certified intro rubric.

## REQ-13 Conclusion checker
**Classification:** PASS  
**Evidence:** `_conclusion` in `engine.py`; Pass2 analysis engine pytest.  
**Risk:** Heuristic.

## REQ-14 Coherence and cohesion
**Classification:** PASS  
**Evidence:** `_coherence`; covered by Pass2 analysis engine pytest (findings categories on full essay).  
**Risk:** Pattern-based, not discourse parser.

## REQ-15 Grammar checker
**Classification:** PARTIAL  
**Evidence:** Heuristic `_grammar` with original/problem/suggestion.  
**Risk:** Not a full grammar engine (LanguageTool-class). Finding shape exists.

## REQ-16 Academic writing checker
**Classification:** PASS  
**Evidence:** `_academic_writing`; eval metrics.

## REQ-17 Readability
**Classification:** PASS  
**Evidence:** `_readability` + explanation on report payload.

## REQ-18 Word count
**Classification:** PARTIAL  
**Evidence:** Total, excl. references, headings, paragraph/sentence counts in extractor/engine. Configurable rules are plan `max_words`, not user-defined counting rules.

## REQ-19 Citation checker
**Classification:** PARTIAL  
**Evidence:** APA7, MLA9, Chicago, Harvard, IEEE in `citations.py`; mismatch test.  
**Missing:** Vancouver, AMA, OSCOLA, Turabian (help text only).

## REQ-20 Reference checker
**Classification:** PASS  
**Evidence:** Extract + missing field detection; mismatch test.

## REQ-21 Source verification
**Classification:** PARTIAL  
**Implementation:** `verify_sources.py`; HTTP `POST /api/citations/verify` with ownership; persists `SourceVerification`.  
**Files:** `backend/app/services/analysis/verify_sources.py`, `backend/app/api/v1/citations.py`  
**Endpoints:** `POST /api/citations/verify`  
**Tests:** `test_citations_are_tenant_isolated`; `test_verification_never_invents_on_empty`  
**Documentation:** citations page disclaimer  
**Risk:** Medium — live Crossref/OpenAlex not certified; monkeypatched in isolation test  
**Remediation:** Live metadata drill; do not treat could_not_verify as fabrication.

## REQ-22 Fabricated citation detection
**Classification:** PARTIAL  
**Evidence:** Cautious statuses; “could not verify” not “fake”; hallucination suite.  
**Missing:** Dedicated impossible-metadata classifier.

## REQ-23 Rubric checker
**Classification:** PARTIAL  
**Evidence:** Paste/manual criteria; engine `_rubric`; disclaimer “AI-assisted rubric assessment”; F1 gate.  
**Missing:** Rubric **file upload**.

## REQ-24 Overall score
**Classification:** PASS  
**Evidence:** Weighted categories; rationale; disclaimer; `test_analysis_engine.py`.

## REQ-25 Priority actions
**Classification:** PASS  
**Evidence:** `_priorities`; report “Fix these first”.

## REQ-26 Fix My Weakest Area
**Classification:** PASS  
**Evidence:** `weakest_area` on analysis result; report UI button; `test_full_analysis_produces_transparent_score` + Pass2 weakest assertions.

## REQ-27 Academic Coach
**Classification:** PARTIAL  
**Evidence:** `POST /api/coach`; UI; disclaimers; no source invention in prompt.  
**Missing:** Coach content pytest; guest heuristic pass-through.

## REQ-28 Improvement modes
**Classification:** PARTIAL  
**Evidence:** Explain / Suggest / Teach / Example on report UI; finding fields.  
**Missing:** Improve Sentence not populated (`improved_sentence` unused in engine).

## REQ-29 AI-writing indicator
**Classification:** PASS  
**Evidence:** Qualitative Low/Moderate/High; disclaimer; no fake %; `AIIndicatorReport`; entitlements.

## REQ-30 Document comparison
**Classification:** PARTIAL  
**Evidence:** `POST /api/analysis/compare`; isolation test; versions page.  
**Missing:** Draft picker; requires both analysed.

## REQ-31 Version history
**Classification:** PARTIAL  
**Evidence:** Create/delete version API; list UI.  
**Missing:** Rename, restore.

## REQ-32 Assignment workspace
**Classification:** PASS  
**Evidence:** `/app/assignments/:id` with question, drafts, analysis links.

## REQ-33 Document upload
**Classification:** PARTIAL  
**Evidence:** DOCX/PDF/TXT/MD/paste; MIME+signature tests. PPTX/ODT/RTF not in allow-list (prepare-only).

## REQ-34 Document processing pipeline
**Classification:** PASS  
**Evidence:** validation → extract → sections/paragraphs → analysis; extractor tests.

## REQ-35 Malicious document protection
**Classification:** PARTIAL  
**Evidence:** Zip bomb, traversal, JS/macro tests. ClamAV optional, **not** required in env.

## REQ-36 Prompt injection protection
**Classification:** PASS  
**Evidence:** `firewall.py`; 1000-case `test_prompt_injection.py`.

## REQ-37 Privacy
**Classification:** PARTIAL  
**Evidence:** Field encryption; HSTS header if production; account/document delete; guest `expires_at`.  
**This pass:** expired guest docs purged on reaper (`purge_expired_guest_documents`, pytest).  
**Missing:** TLS terminator proof; disk/TDE encryption; always-on purge worker independent of analysis jobs.

## REQ-38 AI training privacy
**Classification:** PARTIAL  
**Evidence:** `training_opt_in` default false; copy on help/register.  
**Missing:** Settings toggle; enforcement that no pipeline trains on work.

## REQ-39 User dashboard
**Classification:** PASS  
**Evidence:** `GET /api/dashboard`; `/app/dashboard`.

## REQ-40 Report dashboard
**Classification:** PASS  
**Evidence:** Scores, strengths, weaknesses, findings UI; workflow test.

## REQ-41 Finding structure
**Classification:** PASS  
**Evidence:** Model fields match spec; serialized in reports API.

## REQ-42 Color-coded feedback
**Classification:** PASS  
**Evidence:** Icons + labels; `test_findings_are_not_color_only`.

## REQ-43 Editor
**Classification:** PARTIAL  
**Evidence:** TipTap headings/bold/italic/lists/blockquotes.  
**Missing:** Highlight, comments, citation marks, finding-to-span linking.

## REQ-44 Side-by-side mode
**Classification:** PARTIAL  
**Evidence:** Desktop grid + mobile tabs. Left pane is not live document text.

## REQ-45 PDF report
**Classification:** PASS  
**Evidence:** `build_pdf_report`; download endpoint; disclaimer; `test_pdf_a11y.py`.

## REQ-46 Shareable reports
**Classification:** PASS  
**Evidence:** Password, expiry, revoke, audit; `test_share_link_requires_password_and_can_be_revoked`.

## REQ-47 Authentication
**Classification:** PARTIAL  
**Evidence:** Email/password, verify, reset, sessions, logout, deletion; privileged TOTP MFA enroll/challenge + admin API gate (`test_security_mfa_jwt.py`).  
**Missing:** Google/Apple/Microsoft/University SSO (spec “prepare for”); MFA staging UI drill (HAL-09).

## REQ-48 Guest mode
**Classification:** PASS  
**Evidence:** `POST /api/auth/guest`; `/check` without registration; workflow test.

## REQ-49 Pricing
**Classification:** PASS  
**Evidence:** Free $0 / Student $1.99 / Pro $3.99 / Power $7.99 / Institution custom in `seed.py`; admin plan patch.

## REQ-50 One-time credits
**Classification:** PASS  
**Evidence:** Credit packs; ledger reserve/consume/refund; expiry ledger row; `wallet_matches_ledger`; `test_billing_critical.py` (`ops/cert_pass2_pytest.txt`).

## REQ-51 Global billing
**Classification:** PARTIAL  
**Evidence:** Stripe/Paystack/Flutterwave adapters + webhooks in code.  
**Missing:** Live keys (`ops/cert_payment_keys.json` all false). Dynamic method availability by country is not a live eligibility engine.

## REQ-52 Local currency
**Classification:** PARTIAL  
**Evidence:** Display conversion table, not live FX (matches “do not hardcode into business logic” only partially — rates are static display).

## REQ-53 Payment security
**Classification:** PARTIAL  
**Evidence:** Sandbox scenario suite — all 8 × Stripe/Paystack/Flutterwave (`docs/BILLING_SANDBOX_VERIFICATION.md`); reconcile CLI + mismatch alert (`ops/run_billing_reconcile.py`, `test_billing_reconcile_alert.py`).  
**Missing:** Live/test-key Dashboard charges. **Sandbox-verified; pending live-transaction confirmation of account config before public launch.**

## REQ-54 AI architecture
**Classification:** PASS  
**Evidence:** Provider protocol OpenAI/Anthropic/Gemini; fallback test.

## REQ-55 AI cost control
**Classification:** PARTIAL  
**Evidence:** Plan limits, token budget setting, cache, routing. Per-user cost dashboard incomplete.

## REQ-56 Document chunking
**Classification:** PARTIAL  
**Evidence:** Extractor sections/paragraphs. LLM enhance uses excerpt cap, not full local→global synthesis.

## REQ-57 AI output validation
**Classification:** PASS  
**Evidence:** JSON schema validation; no raw model dump to UI; quality tests.

## REQ-58 AI prompt versioning
**Classification:** PASS  
**Evidence:** `PROMPT_VERSION` on jobs; `prompt_registry.json`.

## REQ-59 Database
**Classification:** PARTIAL  
**Evidence:** Core tables exist; findings consolidated into `analysis_findings`; `sessions` table exists (named `sessions`).  
**Missing:** Separate grammar/structure/argument finding tables (design choice). `notifications` unused.

## REQ-60 Analysis job model
**Classification:** PASS  
**Evidence:** Statuses + model/prompt/tokens/cost/duration/error; queue tests.

## REQ-61 Background processing
**Classification:** PARTIAL  
**Evidence:** Redis+RQ; 1000 jobs 0 lost (`cert_queue_results.json`); Pass3 DLQ `_on_failure` test + `jobs.dead_letter`; SIGTERM graceful stop unit test.  
**Missing:** Staging `REQUIRE_QUEUE`; worker-kill 1 stuck; 5k–50k analysis unrun.

## REQ-62 Real-time status
**Classification:** PASS  
**Evidence:** Polls actual `status`/`stage` from job; `STAGES` in runner; not a fake percent bar.

## REQ-63 Admin dashboard
**Classification:** PARTIAL  
**Evidence:** API overview, users, suspend, plans, flags, eval, security events. Frontend overview counts only.  
**Missing:** Refunds UI, SEO/blog editors, prompt editor, assignment admin.

## REQ-64 SEO strategy (each spec path)
Seeded via `SeoPage` + `frontend/app/[slug]/page.tsx` unless noted.

| ID | Path | Classification | Evidence / gap |
| --- | --- | --- | --- |
| REQ-64.1 | `/ai-essay-checker` | PASS | seeded |
| REQ-64.2 | `/assignment-checker` | PASS | seeded + sitemap |
| REQ-64.3 | `/essay-checker` | PASS | seeded + sitemap |
| REQ-64.4 | `/academic-writing-checker` | PASS | seeded + sitemap |
| REQ-64.5 | `/ai-assignment-checker` | PASS | seeded + `sitemap.ts` + `test_seo_sitemap.py` |
| REQ-64.6 | `/research-paper-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.7 | `/thesis-checker` | PASS | seeded + sitemap |
| REQ-64.8 | `/dissertation-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.9 | `/essay-grammar-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.10 | `/academic-grammar-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.11 | `/essay-structure-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.12 | `/thesis-statement-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.13 | `/argument-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.14 | `/paragraph-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.15 | `/citation-checker` | PASS | seeded + sitemap |
| REQ-64.16 | `/apa-citation-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.17 | `/mla-citation-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.18 | `/harvard-citation-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.19 | `/ai-writing-checker` | PASS | seeded + sitemap + pytest |
| REQ-64.20 | `/grammar-checker` | PASS | seeded + sitemap + pytest |

## REQ-65 Country SEO
**Classification:** PARTIAL  
**Evidence:** GH/NG/KE essay/assignment pages. Spec examples only partially covered; thin-page risk if expanded without content.

## REQ-66 Academic SEO
**Classification:** PARTIAL  
**Evidence:** Citation-style pages + blog. Missing dedicated literature-review/lab-report/reflective/case-study/proposal landings.

## REQ-67 Blog
**Classification:** PARTIAL  
**Evidence:** Seeded educational posts; blog UI; public API cap test. Not all spec article titles exist.

## REQ-68 Technical SEO
**Classification:** PARTIAL  
**Evidence:** sitemap (Pass2 pytest covers REQ-64 slugs), robots, OG, canonical; help FAQPage JSON-LD (`frontend/app/help/page.tsx`, `test_seo_sitemap.py`).  
**Missing:** Breadcrumbs JSON-LD not proven.

## REQ-69 Analytics events
**Classification:** PARTIAL  
**Evidence:** `track()` + `POST /api/public/analytics`; Pass2 server events `citation_check_used`, `payment_failed`, `credit_purchased`, `subscription_started`, `subscription_cancelled` (`test_failed_payment_records_analytics`).  
**Missing:** Funnel warehouse / BI pipeline.

## REQ-70 Privacy-friendly analytics
**Classification:** PASS  
**Evidence:** `public.py` strips text/document/assignment/content.

## REQ-71 Email system
**Classification:** PARTIAL  
**Evidence:** Console/SMTP; verify, reset, subscription confirmed; Pass2 analysis-complete email for registered users (`runner.py`).  
**Missing:** Receipt, usage warning, renewal reminder, cancellation confirmation emails.

## REQ-72 Notifications
**Classification:** FAIL  
**Implementation:** `Notification` model only. No API, no worker, no UI.  
**Evidence:** grep — zero writes.  
**Risk:** Users never see in-app analysis-complete/credits-low events.

## REQ-73 Accessibility
**Classification:** PARTIAL  
**Evidence:** Axe CI + Playwright (public/auth routes); keyboard.spec (login, settings Tab trap, billing); pa11y script; ARIA live/alert patterns; `docs/ACCESSIBILITY_AUDIT.md`.  
**Missing:** Human NVDA/VO/JAWS sign-off (HAL-18). Automated coverage is not that sign-off.

## REQ-74 Mobile-first
**Classification:** PARTIAL  
**Evidence:** Responsive check/report. No automated mobile E2E of the spec workflow.

## REQ-75 Design
**Classification:** PASS  
**Evidence:** Academic visual system in CSS/pages. Spec allowed TipTap; shadcn not used (allowed alternative).

## REQ-76 Landing page
**Classification:** PASS  
**Evidence:** Hero/CTAs/modules match `i18n.ts` spec copy.

## REQ-77 Trust messaging
**Classification:** PASS  
**Evidence:** Landing, footer, report, PDF, help, SEO pages.

## REQ-78 Help center
**Classification:** PASS  
**Evidence:** `/help` topics for files, citations, AI indicator, rubric, privacy, pricing, integrity.

## REQ-79 Security architecture
**Classification:** PARTIAL  
**Evidence:** AuthN/Z, isolation tests, CSRF, rate limit, headers, field crypto, upload tests.  
**Missing:** Independent pentest; secret manager; ClamAV default; malware quarantine.

## REQ-80 Tenant isolation
**Classification:** PASS (repository suite)  
**Evidence:** `test_isolation.py` re-run this engineering pass.  
**Risk:** Not a live-host pentest certificate.

## REQ-81 File security
**Classification:** PASS  
**Evidence:** Size/page/text caps; MIME/signature; `test_document_security.py`.

## REQ-82 API
**Classification:** PARTIAL  
**Evidence:** Auth, assignments, documents, analysis, reports, coach, compare, billing, webhooks exist.  
### REQ-82.1 `GET /api/citations`
**Classification:** PASS  
**Files:** `backend/app/api/v1/citations.py`, `frontend/app/app/assignments/[id]/citations/page.tsx`  
**Endpoints:** `GET /api/citations?document_id=`  
**Tests:** `test_citations_are_tenant_isolated`; OpenAPI path test  
**Risk:** Low  
**Remediation:** none for existence; live Crossref still open (REQ-21).

### REQ-82.2 `POST /api/citations/verify`
**Classification:** PASS  
**Files:** `citations.py`, `verify_sources.py`  
**Endpoints:** `POST /api/citations/verify`  
**Tests:** isolation 404 + never invent (`could_not_verify`, no matched_title)  
**Risk:** Medium — network lookups in production  
**Remediation:** live provider timeout/circuit already in httpx 4s; do not invent.  
Pydantic on write bodies; many responses untyped dicts.

## REQ-83 API documentation
**Classification:** PARTIAL  
**Evidence:** OpenAPI in test/dev; production disabled; core paths pytest. Incomplete schemas.

## REQ-84 Tech stack
**Classification:** PARTIAL  
**Evidence:** Matches preferred stack except no shadcn; RQ not Celery (spec allows either). Dockerfiles exist.

## REQ-85 Frontend routes
**Classification:** PARTIAL  
**Evidence:** `/`, pricing, features, blog, help, `/app/*` assignment routes, coach, settings, billing. SEO slugs via `[slug]`. First-class `/grammar-checker` is slug not a dedicated app route.

## REQ-86 Database performance
**Classification:** PARTIAL  
**Evidence:** Indexes + pagination; EXPLAIN at 100k/1M. 5M/10M unrun.

## REQ-87 Caching
**Classification:** PARTIAL  
**Evidence:** AI cache; SEO revalidate 300s. Citation metadata not a dedicated cache. Private content not publicly cached (code review).

## REQ-88 Error handling
**Classification:** PASS  
**Evidence:** Structured `{error,status}`; no traceback; pytest.

## REQ-89 Observability
**Classification:** PARTIAL  
**Evidence:** structlog + logging hygiene CI; per-endpoint metrics/gauges; `/api/metrics` + prometheus text; OTEL tracing module; Grafana JSON + alert-rules validated (`ops/validate_observability_stack.py`); local observability compose; webhook + PagerDuty Events API v2 code path; `docs/OBSERVABILITY_READINESS.md`.  
**Missing:** Hosted Prometheus/Grafana/Alertmanager (HAL-10); hosted PagerDuty + on-call (HAL-11). Code-complete, pending hosting.

## REQ-90 Rate limiting
**Classification:** PASS  
**Evidence:** Plan-keyed limits; Redis; prod fail-closed.

## REQ-91 AI evaluation system
**Classification:** PARTIAL  
**Evidence:** Eval harness, held-out, CI F1 floors. Lecturer gold n=0; live LLM n=0.

## REQ-92 Human review / QC
**Classification:** FAIL  
**Evidence:** `reviewer_labels.jsonl` empty; no staff review UI. Spec requires admin review of anonymized cases.

## REQ-93 Model fallback
**Classification:** PASS  
**Evidence:** Provider fallback; heuristic report if all fail; injection test.

## REQ-94 Long-document strategy
**Classification:** PASS  
**Evidence:** Plan max_words 2k/10k/25k/50k; entitlement test.

## REQ-95 Credit accounting
**Classification:** PASS  
**Evidence:** Job-tied reserve/consume/refund; billing tests.

## REQ-96 Billing state machine
**Classification:** PARTIAL  
**Evidence:** Payment and credit states; subscription active/cancelled/past_due; Pass2 `invoice.paid` near-expiry extend (`test_invoice_paid_extends_period_near_expiry`).  
**Missing:** `trialing` unused; live provider state sync.

## REQ-97 Data retention
**Classification:** PARTIAL  
**Evidence:** Guest expiry field + **this-pass purge** with pytest. No standalone cron if workers never run. Configurable policy engine incomplete.

## REQ-98 Account deletion
**Classification:** PARTIAL  
**Evidence:** `DELETE /api/auth/me`; clears text/files; **this-pass** cancels active/past_due/trialing subscriptions; pytest.  
**Missing:** Provider-side Stripe cancel; dedicated legal-hold workflow.

## REQ-99 Internationalization
**Classification:** PARTIAL  
**Evidence:** `i18n.ts` English messages object; `User.locale`. No FR/ES/PT/AR/HI.

## REQ-100 Development phases
**Classification:** PARTIAL  
**Phase 1:** Largely implemented (see PASS rows).  
**Phase 2:** Partially in-tree (rubric, coach, compare, credits, indicator, verify service).  
**Phase 3–4:** Not implemented (SSO, LMS, plagiarism vendor, research tools). Spec 108 says do not ship all phases at once.

## REQ-101 Do not build in MVP
**Classification:** PASS  
**Evidence:** No full essay generator, no guaranteed detector, no fake plagiarism DB, no LMS.

## REQ-102 Acceptance test — student workflow
**Classification:** PARTIAL  
**Evidence:** Steps 1–9 partially in `test_api_workflow.py` (paste, not DOCX). Steps 10–15 not automated E2E.

## REQ-103 Additional acceptance tests
**Classification:** PARTIAL  
**Covered:** Guest, isolation, webhooks (pytest), invalid/oversize files, share, prompt injection.  
**Gaps:** DOCX E2E, rubric E2E, AI-indicator E2E, live payment, mobile E2E, citation verify HTTP.

## REQ-104 Final product quality checklist
**Classification:** PARTIAL  
**Evidence:** Unit/integration/a11y/isolation/billing tests exist. Missing: full E2E, CI load, managed backup drill, 90% coverage.

## REQ-105 README
**Classification:** PASS  
**Evidence:** `README.md` contains required sections.

## REQ-106 Final development principle
**Classification:** PARTIAL  
**Evidence:** Core analysis/billing/isolation are real. Placeholders: citations page, notifications, thin admin.

## REQ-107 Future ecosystem integration
**Classification:** FAIL  
**Evidence:** No shared auth/billing code with PDF Tool Hub or other products. Spec is future architecture.

## REQ-108 Build order / launch attributes
**Classification:** PARTIAL  
**Evidence:** Build order was followed in repo history. Attributes “fast, scalable, commercially viable” are **not** proven (p95 fail at 100 in-flight; live billing absent).

---

## Totals (this matrix)

Recount method: every `**Classification:**` line plus each REQ-64 table row. Pass2 promotions: REQ-12/13/14/26 → PASS; REQ-64.5–.20 sitemap gaps → PASS.

| Class | Count |
| --- | ---: |
| PASS | 72 |
| PARTIAL | 57 |
| FAIL | 3 |

FAIL IDs: **REQ-72**, **REQ-92**, **REQ-107**.

Independent auditor rule for **launch**: PARTIAL production requirements that lack live evidence are **launch blockers** even if classified PARTIAL for “code exists.”
