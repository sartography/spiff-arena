from flask import current_app
from flask_mail import Message  # type: ignore


class EmailService:
    """Provides common interface for working with an Email."""

    @staticmethod
    def add_email(
        subject: str,
        sender: str,
        recipients: list[str],
        content: str,
        content_html: str,
        cc: str | None = None,
        bcc: str | None = None,
        reply_to: str | None = None,
        attachment_files: dict | None = None,
    ) -> None:
        """We will receive all data related to an email and send it."""
        mail = current_app.config["MAIL_APP"]

        msg = Message(
            subject,
            sender=sender,
            recipients=recipients,
            body=content,
            html=content_html,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
        )

        if attachment_files is not None:
            for file in attachment_files:
                msg.attach(file["name"], file["type"], file["data"])

        mail.send(msg)
