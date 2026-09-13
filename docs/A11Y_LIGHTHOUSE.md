# Lighthouse Certification Report

Date: 2026-09-07  
Engine: Lighthouse 13.4.1  
**Deployed-URL certificate: not issued.**

## Local public routes (not production, not deployed)

Host: `http://127.0.0.1:3111` (`next dev`). Form factor: Lighthouse default (mobile). Accessibility category:

| Route | Score | Gate 98 |
| --- | ---: | --- |
| `/` | 100 | Pass (local) |
| `/pricing` | 100 | Pass (local) |
| `/login` | 100 | Pass (local) |
| `/register` | 100 | Pass (local) |
| `/check` | 100 | Pass (local) |

Summary: `frontend/a11y/artifacts/lighthouse-summary.json`.

Chrome temp-dir cleanup returned EPERM on this Windows agent after each run; the JSON reports were still written.

## Not executed

- Deployed HTTPS URL
- Production `next start` build
- Authenticated `/app/*` Lighthouse
- Separate desktop form factor
- Mobile + desktop matrix on a public host

CI: `npm run a11y:lighthouse` runs only when `LHCI_URL` is set. It does not skip-pass a missing URL as 98.
