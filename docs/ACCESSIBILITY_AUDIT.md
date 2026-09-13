# Accessibility audit — AcademicCheck AI

Date: 2026-09-07

## Scope of this audit (code / automation)

| Layer | Coverage | Evidence |
| --- | --- | --- |
| axe-core (fixtures) | Static HTML fixtures via `npm run a11y` | CI job `Accessibility axe gate` |
| axe-core (Playwright) | Public + authenticated routes | `frontend/a11y/*.spec.ts`, CI `a11y:playwright` |
| Keyboard-only flows | Login, settings dialog Tab trap, billing focus reach | `frontend/a11y/keyboard.spec.ts` |
| Screen-reader semantics (ARIA) | Live regions / `role="alert"` / `role="status"` on loading, errors, toasts across app pages | Code review + axe; not a human SR session |
| Lighthouse | Script `npm run a11y:lighthouse` when `LHCI_URL` set | `frontend/a11y/lighthouse.mjs` |
| pa11y | `npm run a11y:pa11y` against local base URL | `frontend/a11y/pa11y.mjs` |

## CI enforcement

- `.github/workflows/ci.yml` runs axe fixtures + Playwright a11y (including keyboard specs).
- New pages/components that introduce WCAG 2.2 AA axe violations fail the build.
- pa11y/Lighthouse remain available as scripts; wire `LHCI_URL` / running frontend for full local scans.

## Boundary — human-only remaining item

**This covers full automated and scripted-keyboard coverage.**

The one remaining item that requires a person, not code:

> **Human assistive-technology user sign-off** — real testing with NVDA / VoiceOver / JAWS (or equivalent) by a screen-reader user (HAL-18).

Do not treat this document as that sign-off.
