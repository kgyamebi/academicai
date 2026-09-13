# Accessibility Test Suite

| Layer | Command | Pass rule | What it proves | What it does not prove |
| --- | --- | --- | --- | --- |
| Static source | `pytest -q tests/test_a11y_static.py` | Button types, skip, labels, alerts | TSX contracts | Runtime focus |
| axe-core fixtures | `npm run a11y` | Zero violations, fixture score ≥ 98 | Landmark/ARIA fixtures | Hydrated Next.js DOM |
| Playwright public + auth | `npm run a11y:playwright` | Zero WCAG 2.2 AA axe violations | Live public and `/app/*` including report and admin | NVDA/VoiceOver/JAWS |
| PDF | `pytest -q tests/test_pdf_a11y.py` | Title, language, extractable text | Searchable PDF | PAC / Acrobat |
| Lighthouse | `LHCI_URL=https://… npm run a11y:lighthouse` | category ≥ 0.98 | Only when URL is set | Skipped locally if unset |

CI: fixture axe, Playwright (API started from `a11y/start-api.mjs`), backend PDF test via pytest. Lighthouse is not a silent pass.
