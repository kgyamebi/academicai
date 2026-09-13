# Accessibility testing guide

## Automated (this repository)

```
cd backend && py -3.14 -m pytest tests/test_a11y_static.py tests/test_pdf_a11y.py -q
cd frontend && npm run a11y
cd frontend && npm run a11y:playwright
```

Playwright starts the API on port 8010 and Next on 3100. Do not reuse port 3000.

Lighthouse against a **deployed** origin:

```
cd frontend
$env:LHCI_URL="https://your-deployed-host"
npm run a11y:lighthouse
```

Without `LHCI_URL` the script exits 0 and prints that it skipped. That is not a 98 score.

## Screen readers (required for AA)

Use `docs/ACCESSIBILITY_TESTING_GUIDE.md` in the product help set. Record NVDA, VoiceOver, and JAWS on dashboard, workspace, editor, report, findings, versions, billing, settings, admin.

## Release gates (CI)

- New axe violations fail `npm run a11y` and `npm run a11y:playwright`.
- Lighthouse fails only when `LHCI_URL` is configured and a route is below 0.98.
- Screen-reader and focus regressions are not auto-detectable; they remain a human gate.
