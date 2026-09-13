# WCAG 2.2 AA Mapping

Date: 2026-09-07  
**Decision: not certified.** Mapping is source + live lab axe, not AT sign-off.

| Criterion | Level | Status | Evidence | Gap |
| --- | --- | --- | --- | --- |
| 1.1.1 Non-text | A | Partial | Score ring `aria-label` | PDF not PAC-tagged |
| 1.3.1 Info and Relationships | A | Partial | Landmarks, report tables, list fixes | AT unread |
| 1.4.3 Contrast | AA | Partial | Tokens + local Lighthouse 100 on 5 public routes | Deployed URL unrun |
| 1.4.10 Reflow | AA | Partial | Playwright 320px billing/settings | 400% zoom lab only |
| 1.4.12 Text spacing | AA | Unproven | Not measured | — |
| 2.1.1 Keyboard | A | Partial | Skip, tabs, toolbar, settings Escape | AT unread |
| 2.1.2 No Keyboard Trap | A | Pass (lab) | Dialog Escape restores focus | — |
| 2.4.1 Bypass Blocks | A | Pass (lab) | Skip on public and app shell | Playwright |
| 2.4.3 Focus Order | A | Partial | Dialog restore | — |
| 2.4.6 Headings and Labels | AA | Partial | Live `h1` on auth routes | — |
| 2.4.7 Focus Visible | AA | Pass (source) | `:focus-visible` | — |
| 2.4.11 Focus Not Obscured | AA | Unproven | No sticky overlay | Not measured |
| 2.5.8 Target Size | AA | Partial | App nav ≥44px measured in Playwright | Not all controls pixel-measured |
| 3.2.6 Consistent Help | AA | Pass | Help in header/footer | — |
| 3.3.1 Error Identification | A | Partial | `role="alert"` login/billing | — |
| 3.3.2 Labels or Instructions | A | Partial | Check/coach/password hints | — |
| 3.3.8 Accessible Authentication | AA | Partial | `autocomplete` on auth | — |
| 4.1.2 Name, Role, Value | A | Partial | Live axe auth+public | TipTap residual |
| 4.1.3 Status Messages | AA | Partial | `aria-live` loaders | NVDA not run |

**Compliance claim allowed: none.**
