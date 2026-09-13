# Accessibility Readiness Certificate

Product: AcademicCheck AI  
Date: 2026-09-07  
Standard requested: WCAG 2.2 AA  
Score requested: 98+

**Certificate: not issued.**

Evidence-backed score: **93 / 100**.

## Package

1. Audit — `docs/ACCESSIBILITY.md`
2. WCAG mapping — `docs/WCAG_COMPLIANCE.md`
3. Screen readers — `docs/A11Y_SCREEN_READER.md`
4. Lighthouse — `docs/A11Y_LIGHTHOUSE.md`
5. PDF — `docs/A11Y_PDF.md`
6. Route coverage — `docs/A11Y_ROUTE_COVERAGE.md`
7. Risk register — `docs/A11Y_RISK_REGISTER.md`
8. This certificate

Lab evidence this pass: Playwright axe on public + authenticated routes (including signed-in admin), keyboard/zoom/reflow/44px tests, PDF extract/title/lang tests, local Lighthouse 100 on five public routes.

Still required for 98 and an AA mark: recorded NVDA, VoiceOver, and JAWS; Lighthouse ≥ 0.98 on the **deployed** URL including authenticated routes; PAC or Acrobat on a sample PDF.

Do not print “WCAG 2.2 AA compliant” on the product.
