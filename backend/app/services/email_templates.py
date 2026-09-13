"""HTML email templates — adapted from Invoice App wrapBrand, Scholar Studio branding."""

from __future__ import annotations

from html import escape

from app.config import get_settings

TEAL = "#0f766e"
INK = "#0b1220"
MUTED = "#5c6b7a"
SURFACE = "#f4f6f8"
CARD = "#ffffff"
LINE = "#e2e8f0"


def _wrap(*, title: str, preview: str, body_html: str, text: str, cta_url: str | None = None, cta_label: str = "Continue") -> dict:
    settings = get_settings()
    app = settings.app_name
    origin = settings.app_web_url.rstrip("/")
    cta = ""
    if cta_url:
        cta = (
            f'<p style="margin:28px 0 8px"><a href="{escape(cta_url)}" style="display:inline-block;background:{TEAL};'
            f'color:#ffffff;text-decoration:none;padding:14px 20px;border-radius:10px;font-weight:600;font-size:15px">'
            f"{escape(cta_label)}</a></p>"
        )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:{SURFACE};font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:{INK}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SURFACE};padding:32px 12px">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{CARD};border:1px solid {LINE};border-radius:16px;overflow:hidden">
        <tr><td style="background:{TEAL};color:#ffffff;padding:26px 28px">
          <p style="margin:0;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;opacity:.9">{escape(app)}</p>
          <h1 style="margin:12px 0 0;font-size:24px;line-height:1.25;font-weight:700">{escape(title)}</h1>
          <p style="margin:10px 0 0;font-size:14px;line-height:1.45;opacity:.92">{escape(preview)}</p>
        </td></tr>
        <tr><td style="padding:28px;font-size:15px;line-height:1.6;color:{INK}">
          {body_html}
          {cta}
          <p style="margin-top:24px;font-size:12px;color:{MUTED}">This link expires for your security. If you did not create an account, you can ignore this email.</p>
        </td></tr>
        <tr><td style="padding:18px 28px;background:#f8fafc;color:{MUTED};font-size:12px;line-height:1.5;border-top:1px solid {LINE}">
          Sent by {escape(app)} · <a href="{escape(origin)}" style="color:{TEAL};text-decoration:none">{escape(origin.replace("https://", "").replace("http://", ""))}</a>
          <br/>Support: <a href="{escape(origin)}/contact" style="color:{TEAL}">Contact</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    text_out = f"{title}\n\n{text}"
    if cta_url:
        text_out += f"\n\n{cta_label}: {cta_url}"
    text_out += f"\n\n{app}"
    return {"html": html, "text": text_out}


def verification_email(*, name: str, url: str, hours: int) -> tuple[str, str, str]:
    safe_name = escape(name or "there")
    body = (
        f"<p>Hello {safe_name},</p>"
        f"<p>Confirm ownership of your email address to unlock PDF exports, sharing, and future premium features on AcademicCheck AI.</p>"
        f"<p style=\"font-size:13px;color:{MUTED}\">Link expires in {hours} hours.</p>"
    )
    wrapped = _wrap(
        title="Verify your AcademicCheck AI account",
        preview="Confirm your email to unlock the full workspace.",
        body_html=body,
        text=f"Hello {name or 'there'}, verify your email: {url} (expires in {hours} hours).",
        cta_url=url,
        cta_label="Verify Account",
    )
    return "Verify your AcademicCheck AI account", wrapped["html"], wrapped["text"]


def verification_success_email(*, name: str) -> tuple[str, str, str]:
    settings = get_settings()
    url = f"{settings.app_web_url.rstrip('/')}/app/dashboard"
    body = f"<p>Hello {escape(name or 'there')},</p><p>Your email is verified. You now have full access to exports and sharing on AcademicCheck AI.</p>"
    wrapped = _wrap(
        title="Email verified",
        preview="Your account is confirmed.",
        body_html=body,
        text=f"Hello {name or 'there'}, your email is verified.",
        cta_url=url,
        cta_label="Open workspace",
    )
    return "Your email is verified", wrapped["html"], wrapped["text"]


def password_reset_email(*, url: str, hours: int) -> tuple[str, str, str]:
    body = (
        f"<p>We received a request to reset your password. If you did not ask for this, you can ignore this email.</p>"
        f"<p style=\"font-size:13px;color:{MUTED}\">Link expires in {hours} hours.</p>"
    )
    wrapped = _wrap(
        title="Reset your password",
        preview="Choose a new password for your account.",
        body_html=body,
        text=f"Reset your password: {url}",
        cta_url=url,
        cta_label="Reset password",
    )
    return "Reset your AcademicCheck AI password", wrapped["html"], wrapped["text"]


def email_changed_notice(*, old_email: str, new_email: str) -> tuple[str, str, str]:
    body = (
        f"<p>Your AcademicCheck AI account email was changed from <strong>{escape(old_email)}</strong> "
        f"to <strong>{escape(new_email)}</strong>.</p>"
        f"<p>If you did not make this change, contact support immediately and reset your password.</p>"
    )
    wrapped = _wrap(
        title="Your email address changed",
        preview="Security notice for your account.",
        body_html=body,
        text=f"Your account email changed from {old_email} to {new_email}.",
    )
    return "Your AcademicCheck AI email was changed", wrapped["html"], wrapped["text"]


def email_change_verify(*, name: str, url: str, hours: int) -> tuple[str, str, str]:
    body = (
        f"<p>Hello {escape(name or 'there')},</p>"
        f"<p>Confirm this new email address to finish updating your AcademicCheck AI account.</p>"
        f"<p style=\"font-size:13px;color:{MUTED}\">Link expires in {hours} hours.</p>"
    )
    wrapped = _wrap(
        title="Verify your new email",
        preview="Confirm the new address for your account.",
        body_html=body,
        text=f"Verify your new email: {url}",
        cta_url=url,
        cta_label="Verify new email",
    )
    return "Verify your new AcademicCheck AI email", wrapped["html"], wrapped["text"]


def analysis_ready_email(*, name: str, score: int | float, report_url: str) -> tuple[str, str, str]:
    body = (
        f"<p>Hello {escape(name or 'there')},</p>"
        f"<p>Your AcademicCheck analysis is ready. Overall diagnostic score: "
        f"<strong>{escape(str(score))}</strong>.</p>"
        f"<p style=\"font-size:13px;color:{MUTED}\">This is AI-assisted feedback, not a grade.</p>"
    )
    wrapped = _wrap(
        title="Your analysis is ready",
        preview="Open AcademicCheck to review the report.",
        body_html=body,
        text=f"Your analysis finished with score {score}. Open: {report_url}",
        cta_url=report_url,
        cta_label="Open report",
    )
    return "Your AcademicCheck analysis is ready", wrapped["html"], wrapped["text"]
