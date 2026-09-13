# PDF Accessibility Certification Report

Date: 2026-09-07  
**PAC / Acrobat certificate: not issued.**

## Proven in pytest (`backend/tests/test_pdf_a11y.py`)

| Check | Result |
| --- | --- |
| `%PDF` bytes | Pass |
| Document title metadata | Pass (`AcademicCheck AI — {assignment}`) |
| Language (`/Lang` or `en-GB`) | Pass |
| Extractable text (PyMuPDF `get_text`) | Pass |
| Searchable words (`get_text("words")` > 20) | Pass |
| Heading copy: title, overall score, category scores | Pass |
| Category scores as a table | Pass (ReportLab `Table`) |

## Not executed

| Check | Result |
| --- | --- |
| Acrobat Accessibility Checker | Fail — not run |
| PDF Association PAC | Fail — not run |
| Full PDF/UA tagged structure tree | Fail — Marked flag best-effort; not a tagged UA document |
| Screen-reader reading of the PDF in NVDA/JAWS | Fail — not run |

Treat downloads as **readable, titled, searchable PDFs**, not as PDF/UA certified.
