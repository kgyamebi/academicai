# Accessibility route coverage

Date: 2026-09-07  
Lab: Playwright Chromium + axe-core WCAG 2.2 A/AA tags against `127.0.0.1:3100` with API on `8010`.

| Route | Session | Axe | Keyboard / other |
| --- | --- | --- | --- |
| `/` `/pricing` `/features` `/blog` `/help` `/login` `/register` `/check` | Public | Pass (prior + this suite) | Skip-link, login labels |
| `/app/dashboard` | Registered | Pass | Skip-link, 200%/400% zoom |
| `/app/assignments` | Registered | Pass | — |
| `/app/assignments/[id]` | Registered + seeded report | Pass | — |
| `/app/assignments/[id]/report` | Registered + report id | Pass | Score table, score ring name |
| `/app/assignments/[id]/versions` | Registered | Pass | — |
| `/app/settings` | Registered | Pass | alertdialog Escape |
| `/app/billing` | Registered | Pass | 320px reflow |
| `/app/coach` | Registered | Pass | — |
| `/app/admin` | Student (restricted) | Pass | — |
| `/app/admin` | Bootstrap admin | Pass | No `role=alert` on overview |
| Editor `/check` | Public guest form | Pass | — |

Guest workflow is `/check` (ensureGuest). Comparison page is `/app/assignments/[id]/versions` (product has no `/app/compare`).
