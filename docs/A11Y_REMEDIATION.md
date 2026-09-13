# Accessibility Remediation Report

Date: 2026-09-06

| ID | Issue | Fix | Test | Residual |
| --- | --- | --- | --- | --- |
| A1 | Skip link targeted the whole document | Move `#main-content` to main / app column | `test_skip_link_and_lang_exist` | None in source |
| A2 | Mobile menu had no Escape | `keydown` Escape closes menu; `aria-label` Open/Close | static SiteHeader | Focus not moved into the menu |
| A3 | Check/coach fields lacked ids | `htmlFor` + `id` | static + axe fixtures | — |
| A4 | Billing/admin errors not announced | `role="alert"` / `aria-live` | static | — |
| A5 | Findings color-only chrome | Lucide icon + visible severity + sr-only label | static FindingCard | PDF |
| A6 | Report tabs not keyboardable | Arrow keys, `aria-controls`, tabpanels | report fixture | Focus after “Fix weakest” |
| A7 | Editor shortcuts unnamed | `aria-keyshortcuts` on Bold/Italic | editor fixture | Lexical n/a |
| A8 | No axe CI | `frontend/a11y/scan.mjs` + Playwright | `npm run a11y` / `a11y:playwright` | AT unread |
| A19 | `ul` contained empty-state `<p>` | Empty states outside lists | auth axe | — |
| A20 | Billing error stuck on loading | `role="alert"` when fetch fails | auth axe | — |
| A21 | PDF untitled / unextractable | Title, lang, table, pytest extract | `test_pdf_a11y.py` | PAC/Acrobat |
| A9 | `window.confirm` | Settings `alertdialog` + focus restore | static | AT not run |
| A10 | Editor click-only toolbar | Arrow keys + live status | editor fixture | TipTap AT |
| A11 | Compare as JSON | Accessible table | versions fixture | — |
| A12 | Score cards not tabular | Report `<table>` | report page | — |
| A13 | Small hit targets | `.ac-hit` 44×44 | CSS | Pixel lab |
| A14 | Smooth scroll always | `prefers-reduced-motion` | CSS | — |

No product features were added. No visual redesign beyond accessible names and existing tokens.
