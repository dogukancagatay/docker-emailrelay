import os
import random
import smtplib
import time
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Final, Self, TypeAlias
from urllib.parse import urljoin

import faker
import pytest
import requests
from dotenv import load_dotenv

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

load_dotenv(".env.test")

SMTP_ADDRESS = os.getenv("SMTP_ADDRESS", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", None)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", None)

MAILPIT_API_PORT = os.getenv("MAILPIT_API_PORT", "8025")
MAILPIT_API_URL = os.getenv("MAILPIT_API_URL", f"http://localhost:{MAILPIT_API_PORT}/")

SMTP_SERVER_WAIT_TIMEOUT: Final[int] = 20

MAX_NUM_MESSAGES: Final[int] = 50


@dataclass
class EmailProfile:
    name: str
    email: str


@dataclass
class EmailMessage:
    sender: EmailProfile
    recipient: list[EmailProfile]
    subject: str
    body_text: str
    body_html: str | None = None
    cc: list[EmailProfile] | None = None
    bcc: list[EmailProfile] | None = None
    reply_to: list[EmailProfile] | None = None
    control_str: str | None = None
    message_id: str | None = None


class MailpitClient:
    api_url_prefix = MAILPIT_API_URL
    request_timeout = 10

    def get_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def delete_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = urljoin(self.api_url_prefix, path)
        headers: dict[str, str] = {}

        # Populate headers if provided
        headers |= kwargs.pop("headers", {})

        return requests.request(
            method,
            url,
            headers=headers,
            timeout=kwargs.pop("timeout", self.request_timeout),
            **kwargs,
        )

    def get_messages(self) -> list[str]:
        r = self.get_request(f"/api/v1/messages?limit={MAX_NUM_MESSAGES}")
        assert r.status_code == 200, f"Message list failed: {r.text}"
        messages = r.json()
        return [message["ID"] for message in messages["messages"]]

    def get_message(self, message_id: str) -> EmailMessage:
        r = self.get_request(f"/api/v1/message/{message_id}")
        assert r.status_code == 200, f"Message get failed: {r.text}"
        message = r.json()
        return EmailMessage(
            sender=EmailProfile(message["From"]["Name"], message["From"]["Address"]),
            recipient=[EmailProfile(r["Name"], r["Address"]) for r in message["To"]],
            subject=message["Subject"],
            body_text=message["Text"],
            body_html=message["HTML"] or None,
            cc=[EmailProfile(r["Name"], r["Address"]) for r in message["Cc"]] or None,
            bcc=[EmailProfile(r["Name"], r["Address"]) for r in message["Bcc"]] or None,
            reply_to=[EmailProfile(r["Name"], r["Address"]) for r in message["ReplyTo"]] or None,
            message_id=message["ID"],
        )

    def empty_inbox(self) -> None:
        r = self.delete_request("/api/v1/messages")
        assert r.status_code == 200, f"Message delete failed: {r.text}"


def send_test_email(
    smtp_address: str = "localhost",
    smtp_port: int = 25,
    smtp_username: str | None = SMTP_USERNAME,
    smtp_password: str | None = SMTP_PASSWORD,
    num_messages: int = 1,
    num_recipients: int = 1,
    num_cc: int = 0,
    num_bcc: int = 0,
) -> list[EmailMessage]:
    fake = faker.Faker()

    sender_profile = fake.simple_profile()
    receiver_profiles = [fake.simple_profile() for _ in range(num_recipients)]
    cc_profiles = [fake.simple_profile() for _ in range(num_cc)]
    bcc_profiles = [fake.simple_profile() for _ in range(num_bcc)]

    sent_emails = []

    for _ in range(num_messages):
        control_str = str(uuid.uuid4())

        sender_email: str = sender_profile["mail"]
        sender_name: str = sender_profile["name"]
        subject: str = f"[Test] - {fake.sentence(nb_words=4)}"
        message_text: str = f"This is a test e-mail message with random string {control_str} to check.\n\n"
        message_text += "\n".join(fake.paragraphs(nb=1))

        sender = f"{sender_name} <{sender_email}>"
        receiver = ",".join([f"{r['name']} <{r['mail']}>" for r in receiver_profiles])

        # Construct email body
        email_body = f"Subject: {subject}\nTo: {receiver}\nFrom: {sender}\n"

        if cc_profiles:
            email_body += "Cc: " + ",".join([f"{r['name']} <{r['mail']}>" for r in cc_profiles]) + "\n"

        if bcc_profiles:
            email_body += "Bcc: " + ",".join([f"{r['name']} <{r['mail']}>" for r in bcc_profiles]) + "\n"

        email_body += f"\n{message_text}"

        with smtplib.SMTP(smtp_address, smtp_port) as server:
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)

            server.sendmail(sender, receiver, email_body)

        sent_emails.append(
            EmailMessage(
                sender=EmailProfile(sender_name, sender_email),
                recipient=[EmailProfile(r["name"], r["mail"]) for r in receiver_profiles],
                subject=subject,
                body_text=message_text,
                control_str=control_str,
                cc=[EmailProfile(r["name"], r["mail"]) for r in cc_profiles] or None,
                bcc=[EmailProfile(r["name"], r["mail"]) for r in bcc_profiles] or None,
            )
        )

    return sent_emails


class WaitFor:
    def __init__(self, action: str, timeout_sec: int = 10, poll_sec: int = 1, raise_errors: bool = True) -> None:
        self.timeout_sec = timeout_sec
        self.poll_sec = poll_sec
        self.raise_errors = raise_errors
        self.action = action
        self.start_time = time.monotonic()

    def should_wait(self) -> bool:
        if time.monotonic() - self.start_time + self.poll_sec > self.timeout_sec:
            if self.raise_errors:
                raise TimeoutError(f"Timeout reached while waiting for action: {self.action}")
            return False
        time.sleep(self.poll_sec)
        return True

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return None


@pytest.fixture(name="mailpit")
def fixture_mailpit() -> Generator[MailpitClient, Any, Any]:
    try:
        client = MailpitClient()
        client.empty_inbox()
        assert len(client.get_messages()) == 0, "Message list should be empty"
        yield client
    finally:
        client.empty_inbox()


def test_empty_mailbox(mailpit: MailpitClient) -> None:
    message_id = mailpit.get_messages()
    assert len(message_id) == 0, "Message list should be empty"

    num_messages = random.randint(1, MAX_NUM_MESSAGES)
    send_test_email(SMTP_ADDRESS, SMTP_PORT, num_messages=num_messages)

    with WaitFor("All messages to be received", timeout_sec=SMTP_SERVER_WAIT_TIMEOUT, raise_errors=False) as wait:
        while wait.should_wait():
            if len(mailpit.get_messages()) == num_messages:
                break

    message_ids = mailpit.get_messages()
    assert len(message_ids) == num_messages, f"Expected {num_messages} messages, but found {len(message_ids)}"

    mailpit.empty_inbox()
    message_id = mailpit.get_messages()
    assert len(message_id) == 0, "Message list should be empty"


def test_simple_text_email_fields(mailpit: MailpitClient) -> None:
    email_messages = send_test_email(SMTP_ADDRESS, SMTP_PORT)

    with WaitFor("All messages to be received", timeout_sec=SMTP_SERVER_WAIT_TIMEOUT, raise_errors=False) as wait:
        while wait.should_wait():
            if len(mailpit.get_messages()) == 1:
                break

    mailbox_message_ids = mailpit.get_messages()
    assert len(mailbox_message_ids) == 1, "Message list should have 1 message"

    message = mailpit.get_message(mailbox_message_ids[0])
    email_message = email_messages[0]

    assert message.subject == email_message.subject
    assert message.sender == email_message.sender
    assert message.recipient == email_message.recipient
    assert message.cc == email_message.cc
    assert message.bcc == email_message.bcc
    assert message.reply_to == email_message.reply_to

    assert email_message.control_str is not None
    assert email_message.control_str in message.body_text


def test_text_email_fields_for_multiple_emails(mailpit: MailpitClient) -> None:
    num_messages = random.randint(1, MAX_NUM_MESSAGES)
    email_messages = send_test_email(SMTP_ADDRESS, SMTP_PORT, num_messages=num_messages)

    with WaitFor("All messages to be received", timeout_sec=SMTP_SERVER_WAIT_TIMEOUT, raise_errors=False) as wait:
        while wait.should_wait():
            if len(mailpit.get_messages()) == num_messages:
                break

    mailbox_message_ids = mailpit.get_messages()
    assert len(mailbox_message_ids) == num_messages, f"Expected {num_messages} messages, but found {len(mailbox_message_ids)}"

    # Match each message and check
    for m_id in mailbox_message_ids:
        message = mailpit.get_message(m_id)
        email_message = next(em for em in email_messages if em.control_str and em.control_str in message.body_text)

        assert message.subject == email_message.subject
        assert message.sender == email_message.sender
        assert message.recipient == email_message.recipient
        assert message.cc == email_message.cc
        assert message.bcc == email_message.bcc
        assert message.reply_to == email_message.reply_to

        assert email_message.control_str is not None
        assert email_message.control_str in message.body_text
