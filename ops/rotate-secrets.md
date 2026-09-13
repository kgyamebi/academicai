# Secret rotation

Rotate one class of secret at a time. Do not rotate JWT and payment secrets in the same deploy.

Full injection docs: `docs/SECRETS_MANAGEMENT.md`.

## JWT / session secret

1. Deploy API with `JWT_SECRET_PREVIOUS` set to the outgoing key and `JWT_SECRET_KEY` set to the new ≥32-byte value. `decode_token` accepts both; new tokens are signed only with the current key.
2. Restart API and workers together.
3. After the access/refresh TTL window, remove `JWT_SECRET_PREVIOUS`.
4. Optional: `SECRETS_FILE` JSON (allow-listed keys only) for runtime injection. Existing environment variables win. Missing `SECRETS_FILE` path fails closed.

## Field encryption key

1. Add a re-encrypt job before switching `FIELD_ENCRYPTION_KEY` (keep `FIELD_ENCRYPTION_KEY_PREVIOUS` during dual-read if supported).
2. Do not delete the old key until every encrypted row decrypts with the new key.
3. Losing this key makes student work unreadable — escrow offline.

## Payment webhooks

1. Create a new webhook secret in Stripe / Paystack / Flutterwave.
2. Deploy the new secret.
3. Send a test event.
4. Disable the old secret.

## Sentry / alert webhooks

1. Rotate DSN or incoming webhook in the vendor console.
2. Update `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` / `ALERT_WEBHOOK_URL`.
3. Trigger a test event (`fire_alert` or deliberate 500 in staging).

## Admin bootstrap

1. Remove `ADMIN_BOOTSTRAP_PASSWORD` from the environment after first successful login.
2. Disable any account that still verifies as `ChangeMeAdmin123!`.

## Doppler / Infisical / Railway / Render

1. Rotate in the vendor UI.
2. Sync to runtime env **or** refresh `SECRETS_FILE`.
3. Set `SECRET_MANAGER_URI` to `doppler://…` / `infisical://…` / `railway://…` / `render://…` for audit clarity.
4. Rolling restart API + workers.
