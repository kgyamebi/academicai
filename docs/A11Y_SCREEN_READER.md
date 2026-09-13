# Screen Reader Validation Report

Date: 2026-09-07  
**Result: not certified.**

| Tool | Run? | Pages | Pass/Fail | Severity | Fix | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| NVDA | No | Dashboard, workspace, editor, report, findings, compare, billing, settings, admin | Fail | High for certification | Record NVDA walkthrough on deployed app | Not done |
| VoiceOver | No | Same | Fail | High for certification | Record VoiceOver on iOS/macOS | Not done |
| JAWS | No | Same | Fail | High for certification | JAWS + IE/Chrome on Windows | Not done |

## What was verified instead (not a substitute for AT)

Playwright + axe on live authenticated pages confirmed:

- Landmarks: skip → `#main-content`; each page has `h1` and `main`
- App nav `aria-label="App"` and `aria-current="page"`
- Settings `alertdialog` name, Escape, focus restore
- Report score **table** with caption; score ring `role="img"` + `aria-label`
- Admin heading + restricted alert or overview list
- Coach labelled fields + `aria-live` answer

That proves name/role/value contracts. It does **not** prove NVDA browse/focus mode, VoiceOver rotor, or JAWS virtual cursor announcements.

JAWS-compatible standards in source: native tables with `scope`, `alertdialog`, `tablist`/`tab`/`tabpanel`, `aria-live` on loaders. Untested with JAWS.
