# Accessibility risk register

Date: 2026-09-07

| Risk | Likelihood | Impact | Severity | Treatment |
| --- | --- | --- | --- | --- |
| Screen-reader regression undiscovered | High until AT run | High (cannot claim AA) | High | Commission NVDA + VoiceOver + JAWS recordings |
| Deployed contrast/CSP differs from lab | Medium | Medium | Medium | Lighthouse on production URL with `LHCI_URL` |
| PDF fails PAC despite extractable text | High | Medium for institutions | Medium | Acrobat/PAC on a sample download; tagged PDF/UA if required by contract |
| TipTap editor quirks | Medium | Medium | Medium | Already keyboard-tooled; AT still unsigned |
| Next.js overlay false axe hangs | Low after exclude | Low | Low | axe excludes `nextjs-portal`; `devIndicators: false` |
| Auth axe not run in CI if Python missing | Medium | High (gate bypass) | Medium | Frontend CI now installs API deps and starts uvicorn |
