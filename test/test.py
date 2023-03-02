import os
import smtplib
import string
import sys
import time
import uuid

import faker
import requests


API_TOKEN = os.getenv("MAILTRAP_API_TOKEN", None)
USERNAME = os.getenv("MAILTRAP_USERNAME", None)
PASSWORD = os.getenv("MAILTRAP_PASSWORD", None)

MAILTRAP_ACCOUNTS_API_URL = "https://mailtrap.io/api/accounts"

EMAIL_BODY_TEMPLATE = string.Template(
    """\
Subject: $subject
To: $receiver
From: $sender

$message_text
"""
)


def write_config(client_username: str, client_password: str) -> None:
    with open("config/client-auth.txt", mode="w") as f:
        f.write(f"client plain {client_username} {client_password}")

    with open("config/server-auth.txt", mode="w") as f:
        f.write("")


def get_account_id(api_url_prefix: str, api_token: str) -> int:

    headers = {
        "Api-Token": api_token,
        "Content-Type": "application/json",
    }

    r = requests.get(f"{api_url_prefix}", headers=headers)
    assert r.status_code == 200

    account_list = r.json()
    assert len(account_list) > 0

    assert "id" in account_list[0]
    assert account_list[0] is not None
    account_id = account_list[0]["id"]

    return account_id


def get_inbox_list(api_url_prefix: str, api_token: str, account_id: int) -> list:

    headers = {
        "Api-Token": api_token,
        "Content-Type": "application/json",
    }

    r = requests.get(f"{api_url_prefix}/{account_id}/inboxes", headers=headers)
    assert r.status_code == 200

    inbox_list = r.json()

    assert inbox_list is not None
    assert len(inbox_list) > 0

    return inbox_list


def delete_message_from_inbox(
    api_url_prefix: str, api_token: str, account_id: int, inbox_id: int, message_id: int
):
    headers = {
        "Api-Token": api_token,
        "Content-Type": "application/json",
    }

    r = requests.delete(
        f"{api_url_prefix}/{account_id}/inboxes/{inbox_id}/messages/{message_id}",
        headers=headers,
    )
    assert r.status_code == 200, f"Message delete failed: {r.text}"


def get_messages_from_inbox(
    api_url_prefix: str, api_token: str, account_id: int, inbox_id: str
) -> list:

    headers = {
        "Api-Token": api_token,
        "Content-Type": "application/json",
    }

    # Get Messages
    r = requests.get(
        f"{api_url_prefix}/{account_id}/inboxes/{inbox_id}/messages", headers=headers
    )
    assert r.status_code == 200

    message_list = r.json()
    assert message_list is not None

    return message_list


def send_test_email(
    smtp_address: str = "localhost",
    smtp_port: int = 25,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
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
    message_text: str = (
        f"This is a test e-mail message with random string {control_str} to check.\n\n"
    )
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


def get_message_from_inbox(
    api_url_prefix: str, api_token: str, account_id: int, inbox_id: str, message_id: str
) -> tuple[dict, str]:

    headers = {
        "Api-Token": api_token,
        "Content-Type": "application/json",
    }

    # Get message json
    r = requests.get(
        f"{api_url_prefix}/{account_id}/inboxes/{inbox_id}/messages/{message_id}",
        headers=headers,
    )
    assert r.status_code == 200, f"Message detail request failed: {r.text}"

    message = r.json()
    assert message is not None, "Received message object cannot be None"

    # Get message body
    r = requests.get(
        f"{MAILTRAP_ACCOUNTS_API_URL}/{account_id}/inboxes/{inbox_id}/messages/{message_id}/body.txt",
        headers=headers,
    )
    assert r.status_code == 200

    message_body = r.text
    assert (
        message_body is not None and len(message_body) > 0
    ), "Message body cannot be Empty"

    return message, message_body


def empty_inbox(
    api_url_prefix: str, api_token: str, account_id: int, inbox_id: str
) -> None:

    message_list = get_messages_from_inbox(
        api_url_prefix, api_token, account_id, inbox_id
    )
    if message_list:
        print(f"There are messages ({len(message_list)}) in the inbox, will empty")

    # Delete messages
    for message in get_messages_from_inbox(
        api_url_prefix, api_token, account_id, inbox_id
    ):
        assert "id" in message

        print(f"Deleting message({message['id']}) from inbox({inbox_id})")
        delete_message_from_inbox(
            api_url_prefix, api_token, account_id, inbox_id, message["id"]
        )


if __name__ == "__main__":

    for p in [API_TOKEN, USERNAME, PASSWORD]:
        if not p:
            print(
                "ERROR: Cannot continue without MAILTRAP_API_TOKEN, MAILTRAP_USERNAME, MAILTRAP_PASSWORD environment variables"
            )
            sys.exit(1)

    write_config(USERNAME, PASSWORD)

    print("Get the account id")
    account_id = get_account_id(MAILTRAP_ACCOUNTS_API_URL, API_TOKEN)

    print(f"Obtain inbox list of account({account_id})")
    inbox_list = get_inbox_list(MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id)

    # Get the inbox_id of the first inbox
    assert inbox_list[0] is not None
    for field in ["id", "username", "password", "domain"]:
        assert field in inbox_list[0]

    inbox_id = inbox_list[0]["id"]
    smtp_username = inbox_list[0]["username"]
    smtp_password = inbox_list[0]["password"]

    print(f"Check for residual messages in the inbox({inbox_id})")
    empty_inbox(MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id, inbox_id)

    print("Send test email")
    (
        control_str,
        subject,
        sender_email,
        sender_name,
        receiver_email,
        receiver_name,
    ) = send_test_email("localhost", 9025)
    print("Wait for 10 secs...")
    time.sleep(10)

    # Check inbox for new email messages
    print("Check inbox for new messages")
    new_message_list = get_messages_from_inbox(
        MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id, inbox_id
    )
    assert new_message_list is not None, "Messages gathered from inbox cannot be None"
    assert (
        len(new_message_list) == 1
    ), f"Number of messages in the inbox is not 1 ({len(new_message_list)})"
    assert "id" in new_message_list[0]

    print("Getting the message")
    new_message_list = get_messages_from_inbox(
        MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id, inbox_id
    )
    # Get message details and body
    message_id = new_message_list[0]["id"]
    message, message_body = get_message_from_inbox(
        MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id, inbox_id, message_id
    )

    print("Checking message details")
    # Check received message details
    assert (
        message["subject"] == subject
    ), f"Received email subject({message['subject']}) is different from expected value({subject})"
    assert (
        message["from_email"] == sender_email
    ), f"{message['from_email']} != {sender_email}"
    assert message["from_name"] == sender_name
    assert message["to_email"] == receiver_email
    assert message["to_name"] == receiver_name
    assert control_str in message_body, f"'{control_str}' is not in '{message_body}'"

    print(f"Will cleanup inbox({inbox_id})")
    empty_inbox(MAILTRAP_ACCOUNTS_API_URL, API_TOKEN, account_id, inbox_id)

    print("Done")
