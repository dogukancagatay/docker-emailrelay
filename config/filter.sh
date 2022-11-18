#!/bin/bash

#############################################################################
CONTENT_FILE="${1}"
ENVELOPE_FILE="${2}"

FROM="$(awk '/X-MailRelay-From:/ {print $2;exit}' \"${ENVELOPE_FILE}\")"
TO="$(awk '/X-MailRelay-To-Remote:/ {print $2;exit}' \"${ENVELOPE_FILE}\")"
CLIENT_IP="$(awk '/MailRelay-Client:/ {print $2;exit}' \"${ENVELOPE_FILE}\")"
#############################################################################


BLOCKED_FROM_EMAIL="blocked-1@example.org blocked-2@example.org blocked-3@example.org"

for BLOCKED_EMAIL in $BLOCKED_FROM_EMAIL
do
  if [[ $FROM =~ $BLOCKED_EMAIL ]]; then
    echo "<<You cannot send e-mail from address: $BLOCKED_EMAIL >>"
    exit 1  # <= cancel further processing by emailrelay (send error code)
    # exit 100  # <= cancel further processing by emailrelay (forget email, silent rejection)
  fi
done

exit 0 # <= continue processing
