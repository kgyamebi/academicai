"""Outbound email delivery + SMTP config gates + queue metrics."""

from unittest.mock import MagicMock, patch

import pytest

from app.config import get_settings
from app.core.metrics import snapshot
from app.services.emailer import (
    ConsoleEmailProvider,
    SMTPEmailProvider,
    assert_smtp_config,
    deliver_email_now,
    get_email_provider,
    invalidate_smtp_probe_cache,
    send_email,
    send_email_strict,
    smtp_delivery_ready,
    smtp_status,
)


def test_console_provider_in_test(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    provider = get_email_provider()
    assert isinstance(provider, ConsoleEmailProvider)
    provider.send("a@b.com", "subj", "body", html="<p>x</p>")


def test_console_refused_in_production(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    monkeypatch.setattr(get_settings(), "app_env", "production")
    with pytest.raises(RuntimeError, match="not allowed in production"):
        ConsoleEmailProvider().send("a@b.com", "subj", "body")


def test_assert_smtp_config_requires_host(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        assert_smtp_config()


def test_assert_smtp_config_ok(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    assert_smtp_config()


def test_smtp_provider_requires_host(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "")
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        get_email_provider()


def test_smtp_delivery_ready_console_non_prod(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    monkeypatch.setattr(get_settings(), "app_env", "development")
    assert smtp_delivery_ready() is True


def test_smtp_delivery_ready_console_prod(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    monkeypatch.setattr(get_settings(), "app_env", "production")
    assert smtp_delivery_ready() is False


def test_send_email_does_not_raise_on_smtp_failure(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "email_async", False)

    class Boom(SMTPEmailProvider):
        def send(self, to, subject, body, html=None):
            raise RuntimeError("boom")

    with patch("app.services.emailer.get_email_provider", return_value=Boom()):
        with patch("app.services.emailer.allow", return_value=True):
            send_email("a@b.com", "subj", "body")  # must not raise


def test_send_email_strict_raises(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")

    class Boom(SMTPEmailProvider):
        def send(self, to, subject, body, html=None):
            raise RuntimeError("boom")

    with patch("app.services.emailer.get_email_provider", return_value=Boom()):
        with patch("app.services.emailer.allow", return_value=True):
            with pytest.raises(RuntimeError, match="boom"):
                send_email_strict("a@b.com", "subj", "body")


def test_smtp_probe_uses_connect(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "smtp_port", 587)
    monkeypatch.setattr(get_settings(), "smtp_user", "")
    monkeypatch.setattr(get_settings(), "smtp_tls", "auto")
    monkeypatch.setattr(get_settings(), "app_env", "test")
    provider = SMTPEmailProvider()
    smtp = MagicMock()
    with patch.object(provider, "_connect_and", side_effect=lambda action: action(smtp)):
        assert provider.probe() is True
        smtp.noop.assert_called_once()


def test_tls_mode_disabled_blocked_in_production(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "smtp_tls", "disabled")
    monkeypatch.setattr(get_settings(), "app_env", "production")
    monkeypatch.setattr(get_settings(), "smtp_user", "u")
    monkeypatch.setattr(get_settings(), "smtp_password", "p")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    with pytest.raises(RuntimeError, match="not allowed in production"):
        SMTPEmailProvider()._tls_mode()


def test_build_message_includes_list_unsubscribe(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_from", "AcademicCheck <noreply@academiccheck.ai>")
    monkeypatch.setattr(get_settings(), "app_web_url", "https://app.example")
    monkeypatch.setattr(get_settings(), "email_reply_to", "support@academiccheck.ai")
    from app.services.emailer import _build_message

    msg = _build_message(to="a@b.com", subject="Hi", body="plain", html="<p>x</p>")
    assert "List-Unsubscribe" in msg
    assert "List-Unsubscribe-Post" in msg
    assert "support@academiccheck.ai" in msg["Reply-To"]
    assert "noreply@academiccheck.ai" in msg["From"]


def test_assert_smtp_requires_auth_in_production(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    monkeypatch.setattr(get_settings(), "app_env", "production")
    monkeypatch.setattr(get_settings(), "smtp_user", "")
    monkeypatch.setattr(get_settings(), "smtp_password", "")
    monkeypatch.setattr(get_settings(), "smtp_tls", "required")
    with pytest.raises(RuntimeError, match="SMTP_USER"):
        assert_smtp_config()


def test_deliver_increments_metrics(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    monkeypatch.setattr(get_settings(), "app_env", "test")
    before = snapshot().get("email.sent", 0)
    deliver_email_now("a@b.com", "subj", "body")
    assert snapshot().get("email.sent", 0) >= before + 1


def test_send_email_queues_when_async(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_async", True)
    with patch("app.workers.queue.enqueue_email", return_value=True) as enq:
        send_email("a@b.com", "subj", "body", html="<p>x</p>")
        enq.assert_called_once()
    assert snapshot().get("email.queued", 0) >= 1


def test_smtp_status_includes_envelope(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    monkeypatch.setattr(get_settings(), "email_envelope_from", "bounces@academiccheck.ai")
    invalidate_smtp_probe_cache()
    with patch("app.services.emailer.SMTPEmailProvider.probe", return_value=True):
        status = smtp_status()
    assert status["envelope_from"] == "bounces@academiccheck.ai"
    assert status["async"] is False  # conftest sets EMAIL_ASYNC=false


def test_resend_provider_requires_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "resend")
    monkeypatch.setattr(get_settings(), "email_api_key", "")
    monkeypatch.setattr(get_settings(), "resend_api_key", "")
    with pytest.raises(RuntimeError, match="EMAIL_API_KEY"):
        get_email_provider()


def test_resend_send_posts_api(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "resend")
    monkeypatch.setattr(get_settings(), "email_api_key", "re_test_key")
    monkeypatch.setattr(get_settings(), "email_from", "onboarding@resend.dev")
    from app.services.emailer import ResendEmailProvider

    provider = ResendEmailProvider()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.post.return_value = mock_response
    with patch("httpx.Client", return_value=mock_client):
        provider.send("a@b.com", "Hi", "plain", html="<p>x</p>")
    args, kwargs = mock_client.post.call_args
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["json"]["to"] == ["a@b.com"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")


def test_smtp_send_uses_envelope(monkeypatch):
    monkeypatch.setattr(get_settings(), "email_provider", "smtp")
    monkeypatch.setattr(get_settings(), "smtp_host", "smtp.example.com")
    monkeypatch.setattr(get_settings(), "smtp_port", 587)
    monkeypatch.setattr(get_settings(), "smtp_tls", "disabled")
    monkeypatch.setattr(get_settings(), "app_env", "development")
    monkeypatch.setattr(get_settings(), "email_from", "noreply@academiccheck.ai")
    monkeypatch.setattr(get_settings(), "email_envelope_from", "bounces@academiccheck.ai")
    monkeypatch.setattr(get_settings(), "smtp_user", "")
    provider = SMTPEmailProvider()
    captured = {}

    def _fake_connect(action):
        smtp = MagicMock()

        def send_message(msg, from_addr=None, to_addrs=None):
            captured["from_addr"] = from_addr
            captured["to_addrs"] = to_addrs

        smtp.send_message.side_effect = send_message
        action(smtp)

    with patch.object(provider, "_connect_and", side_effect=_fake_connect):
        provider.send("user@gmail.com", "Hi", "body")
    assert captured["from_addr"] == "bounces@academiccheck.ai"
    assert captured["to_addrs"] == ["user@gmail.com"]
