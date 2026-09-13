# Developer Accessibility Standards

- Every `<button>` has `type="button"` or `type="submit"`.
- Every control has a visible name (label or text). No clickable `div`/`span`.
- Interactive hit area uses `.ac-hit` (44×44).
- Errors use `role="alert"` and `aria-invalid` / `aria-describedby`.
- New dialogs need `role="alertdialog"` or `dialog`, Escape, and focus restore. Do not use `window.confirm`.
- Score and severity never use color alone.
- Add a fixture under `frontend/a11y/fixtures` and keep `npm run a11y` at 98+.
- Public and authenticated `/app/*` routes must stay clean under `npm run a11y:playwright`.
