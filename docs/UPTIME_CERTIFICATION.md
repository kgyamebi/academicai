# Uptime Certification

Date: 2026-09-07  
Artifact: `ops/cert_uptime_window.json`

| Window | Availability | Error budget | Status |
| --- | --- | --- | --- |
| 60 seconds (46 samples, 1 Hz) | live **1.000**, ready **1.000** | n/a | Measured |
| 7 days | — | — | **not_measured** |
| 30 days | — | — | **not_measured** |
| 90 days | — | — | **not_measured** |

`slo_99_95_supported: false`

99.95% over 30 days allows ~21.6 minutes of downtime. A 60-second local probe cannot support that SLO.

Do not extrapolate 1.0 × 60 s into monthly availability.
