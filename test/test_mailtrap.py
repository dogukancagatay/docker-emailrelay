import os
import smtplib
import string
import sys
import time
import uuid
from typing import Any, TypeAlias, cast
from urllib.parse import urljoin

import faker
import requests

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


USERNAME = os.getenv("MAILTRAP_USERNAME", None)
PASSWORD = os.getenv("MAILTRAP_PASSWORD", None)

SMTP_ADDRESS = os.getenv("SMTP_ADDRESS", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", None)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", None)

EMAIL_BODY_TEMPLATE = string.Template(
    """\
Subject: $subject
To: $receiver
From: $sender

$message_text
"""
)


def write_config(client_username: str, client_password: str) -> None:
    with open("config/client-auth.txt", mode="w", encoding="UTF-8") as f:
        f.write(f"client plain {client_username} {client_password}")

    with open("config/server-auth.txt", mode="w", encoding="UTF-8") as f:
        f.write("")


class MailtrapClient:
    api_url_prefix: str = "https://mailtrap.io/"
    api_token: str | None = os.getenv("MAILTRAP_API_TOKEN", None)
    request_timeout = 10

    def __init__(self):
        if not self.api_token:
            print("ERROR: Cannot continue without MAILTRAP_API_TOKEN environment variable")
            sys.exit(2)

    def get_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def delete_request(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = urljoin(self.api_url_prefix, path)
        headers: dict[str, str] = {
            "Api-Token": cast(str, self.api_token),
        }

        # Populate headers if provided
        headers.update(kwargs.pop("headers", {}))

        return requests.request(
            method,
            url,
            headers=headers,
            timeout=kwargs.pop("timeout", self.request_timeout),
            **kwargs,
        )

    def get_account_id(self) -> str:
        r = self.get_request("/api/accounts")
        assert r.status_code == 200

        account_list = r.json()
        assert len(account_list) > 0

        assert "id" in account_list[0]
        assert account_list[0] is not None
        return str(account_list[0]["id"])

    def get_inbox_list(self, account_id: str) -> JSON:
        r = self.get_request(f"/api/accounts/{account_id}/inboxes")
        assert r.status_code == 200

        inbox_list: JSON = r.json()

        assert inbox_list is not None
        assert len(inbox_list) > 0

        return inbox_list

    def delete_message_from_inbox(self, account_id: str, inbox_id: str, message_id: str) -> None:
        r = self.delete_request(f"/api/accounts/{account_id}/inboxes/{inbox_id}/messages/{message_id}")
        assert r.status_code == 200, f"Message delete failed: {r.text}"

    def get_messages_from_inbox(self, account_id: str, inbox_id: str) -> JSON:
        # Get Messages
        r = self.get_request(f"/api/accounts/{account_id}/inboxes/{inbox_id}/messages")
        assert r.status_code == 200

        message_list: JSON = r.json()
        assert message_list is not None

        return message_list

    def get_message_from_inbox(self, account_id: str, inbox_id: str, message_id: str) -> tuple[JSON, str]:
        # Get message json
        r = self.get_request(f"/api/accounts/{account_id}/inboxes/{inbox_id}/messages/{message_id}")
        assert r.status_code == 200, f"Message detail request failed: {r.text}"

        message: JSON = r.json()
        assert message is not None, "Received message object cannot be None"

        # Get message body
        r = self.get_request(f"/api/accounts/{account_id}/inboxes/{inbox_id}/messages/{message_id}/body.txt")
        assert r.status_code == 200

        message_body: str = r.text
        assert message_body is not None, "Message body cannot be empty"
        assert len(message_body) > 0, "Message body cannot be empty"

        return message, message_body

    def empty_inbox(self, account_id: str, inbox_id: str) -> None:
        messages = self.get_messages_from_inbox(account_id, inbox_id)
        if messages:
            print(f"There are messages ({len(messages)}) in the inbox, will empty")

        # Delete messages
        for message in messages:
            assert "id" in message

            print(f"Deleting message({message['id']}) from inbox({inbox_id})")
            self.delete_message_from_inbox(account_id, inbox_id, message["id"])


def send_test_email(
    smtp_address: str = "localhost",
    smtp_port: int = 25,
    smtp_username: str | None = SMTP_USERNAME,
    smtp_password: str | None = SMTP_PASSWORD,
) -> tuple[str, str, str, str, str, str]:
    fake = faker.Faker()

    sender_profile = fake.simple_profile()
    receiver_profile = fake.simple_profile()

    control_str = str(uuid.uuid4())

    sender_email: str = sender_profile["mail"]
    sender_name: str = sender_profile["name"]
    receiver_email: str = receiver_profile["mail"]
    receiver_name: str = receiver_profile["name"]
    subject: str = f"[Test] - {fake.sentence(nb_words=4)}"
    message_text: str = f"This is a test e-mail message with random string {control_str} to check.\n\n"
    message_text += "\n".join(fake.paragraphs(nb=1))

    sender = f"{sender_name} <{sender_email}>"
    receiver = f"{receiver_name} <{receiver_email}>"
    message_body = EMAIL_BODY_TEMPLATE.substitute(
        sender=sender,
        receiver=receiver,
        subject=subject,
        message_text=message_text,
    )

    with smtplib.SMTP(smtp_address, smtp_port) as server:
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        server.sendmail(sender, receiver, message_body)
        print(f"Test email sent with subject: '{subject}'")

    return (
        control_str,
        subject,
        sender_email,
        sender_name,
        receiver_email,
        receiver_name,
    )


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("ERROR: Cannot continue without MAILTRAP_USERNAME, MAILTRAP_PASSWORD environment variables")
        sys.exit(1)

    write_config(USERNAME, PASSWORD)

    mailtrap = MailtrapClient()

    print("Get the account id")
    account_id = mailtrap.get_account_id()

    print(f"Obtain inbox list of account({account_id})")
    inbox_list = mailtrap.get_inbox_list(account_id)

    # Get the inbox_id of the first inbox
    assert inbox_list[0] is not None
    for field in ["id", "username", "password", "domain"]:
        assert field in inbox_list[0]

    inbox_id = inbox_list[0]["id"]
    smtp_username = inbox_list[0]["username"]
    smtp_password = inbox_list[0]["password"]

    print(f"Check for residual messages in the inbox({inbox_id})")
    mailtrap.empty_inbox(account_id, inbox_id)

    print("Send test email")
    (
        control_str,
        subject,
        sender_email,
        sender_name,
        receiver_email,
        receiver_name,
    ) = send_test_email(SMTP_ADDRESS, SMTP_PORT)
    print("Wait for 10 secs...")
    time.sleep(10)

    # Check inbox for new email messages
    print("Check inbox for new messages")
    new_message_list = mailtrap.get_messages_from_inbox(account_id, inbox_id)
    assert new_message_list is not None, "Messages gathered from inbox cannot be None"
    assert len(new_message_list) == 1, f"Number of messages in the inbox is not 1 ({len(new_message_list)})"
    assert "id" in new_message_list[0]

    print("Getting the message")
    new_message_list = mailtrap.get_messages_from_inbox(account_id, inbox_id)
    # Get message details and body
    message_id = new_message_list[0]["id"]
    message, message_body = mailtrap.get_message_from_inbox(account_id, inbox_id, message_id)

    print("Checking message details")
    # Check received message details
    assert (
        message["subject"] == subject
    ), f"Received email subject({message['subject']}) is different from expected value({subject})"
    assert message["from_email"] == sender_email, f"{message['from_email']} != {sender_email}"
    assert message["from_name"] == sender_name
    assert message["to_email"] == receiver_email
    assert message["to_name"] == receiver_name
    assert control_str in message_body, f"'{control_str}' is not in '{message_body}'"

    print(f"Will cleanup inbox({inbox_id})")
    mailtrap.empty_inbox(account_id, inbox_id)

    print("Done")
