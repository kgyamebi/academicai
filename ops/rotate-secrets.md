# Secret rotation

Rotate one class of secret at a time. Do not rotate JWT and payment secrets in the same deploy.

## JWT / session secret

1. Deploy API that accepts `JWT_SECRET_KEY` and `JWT_SECRET_PREVIOUS` (add previous only if dual-verify is implemented; otherwise warn users they will be signed out).
2. Set `JWT_SECRET_KEY` to a new ≥32-byte random value.
3. Restart API and workers together.
4. Existing cookies become invalid. That is intended.

## Field encryption key

1. Add a re-encrypt job before switching `FIELD_ENCRYPTION_KEY`.
2. Do not delete the old key until every `enc:v1:` row decrypts with the new key.
3. Losing this key makes student work unreadable.

## Payment webhooks

1. Create a new webhook secret in Stripe / Paystack / Flutterwave.
2. Deploy the new secret.
3. Send a test event.
4. Disable the old secret.

## Admin bootstrap

1. Remove `ADMIN_BOOTSTRAP_PASSWORD` from the environment after first successful login.
2. Disable any account that still verifies as `ChangeMeAdmin123!`.
