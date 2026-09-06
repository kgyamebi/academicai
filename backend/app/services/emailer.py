from email.message import EmailMessage

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger("email")


class EmailProvider:
    def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    def send(self, to: str, subject: str, body: str) -> None:
        log.info("email_console", to=to, subject=subject)
        print(f"\n--- EMAIL to {to} ---\n{subject}\n{body}\n--- END EMAIL ---\n")


class SMTPEmailProvider(EmailProvider):
    def send(self, to: str, subject: str, body: str) -> None:
        import smtplib

        settings = get_settings()
        msg = EmailMessage()
        msg["From"] = settings.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)


def get_email_provider() -> EmailProvider:
    settings = get_settings()
    if settings.email_provider == "smtp" and settings.smtp_host:
        return SMTPEmailProvider()
    return ConsoleEmailProvider()


def send_email(to: str, subject: str, body: str) -> None:
    get_email_provider().send(to, subject, body)
