# Secrets management — AcademicCheck AI

## Principles

- Never commit secrets to git.
- Never hardcode production keys in source.
- Prefer platform secret stores; inject as env or `SECRETS_FILE` JSON.
- Rotate one secret class per deploy (`ops/rotate-secrets.md`).

## Supported injection paths

| Source | How |
| --- | --- |
| Railway / Render / Vercel env | Set allow-listed keys as variables |
| Doppler / Infisical | Sync to process env **or** export JSON → `SECRETS_FILE` |
| AWS Secrets Manager / GCP / Vault | CSI mount JSON file → `SECRETS_FILE` |
| Local file | `SECRET_MANAGER_URI=file:///path/secrets.json` + `SECRETS_FILE` |

Set `SECRET_MANAGER_URI` to document the source of truth:

`doppler://`, `infisical://`, `aws-secretsmanager://`, `gcp-secretmanager://`, `vault://`, `railway://`, `render://`, `file://`

Application code validates the URI prefix and loads **only allow-listed keys** from `SECRETS_FILE` into empty env slots (`backend/app/core/secrets.py`). Existing env wins.

## Allow-listed keys

JWT, app secret, field encryption (+ previous), DB/Redis URLs, payment secrets, AI keys, S3, Sentry, SMTP password, alert/PagerDuty, backup encryption.

Unknown keys in the JSON file are ignored (fail closed against accidental dump of unrelated secrets into the process).

## Rotation quick reference

1. **JWT** — set `JWT_SECRET_PREVIOUS`, deploy new `JWT_SECRET_KEY`, wait TTL, remove previous.
2. **Field encryption** — re-encrypt rows before retiring old key; losing the key loses drafts.
3. **Payment webhooks** — dual-secret window at the provider, then cut over.
4. **Sentry / alerts** — rotate DSN/webhook in the vendor UI, then update env.

## Soft-launch checklist

- [ ] Production secrets only in the manager / platform
- [ ] `FIELD_ENCRYPTION_KEY` escrowed offline for DR
- [ ] `ADMIN_BOOTSTRAP_PASSWORD` removed after first admin login
- [ ] No `.env` with live PSP keys on developer laptops for shared demos
