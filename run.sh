#!/bin/sh

if [ -z "${EMAILRELAY_OPTS}" ]; then
    echo "FATAL: The EMAILRELAY_OPTS environment variable is NOT defined"
    exit 2
fi

exec /usr/sbin/emailrelay --no-daemon --no-syslog --log \
  --remote-clients --port "${PORT:-587}" ${EMAILRELAY_OPTS}
