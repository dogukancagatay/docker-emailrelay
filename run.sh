#!/bin/sh
set -e

# Some (hopefully) sensible defaults. Users don't have to specify those.
DEFAULT_OPTS=${DEFAULT_OPTS:---no-daemon --no-syslog --log --remote-clients --port "${PORT:-587}"}

# Running this image without any command-line argument doesn't make sense
if [ -z "$*" ]; then
    echo "FATAL: Please provide some command-line arguments to emailrelay"
    echo "E.g., -D msa.example.com --immediate --forward-to mail.example.org:smtp"
    echo "Note, we already pass ${DEFAULT_OPTS}"
    exit 2
fi

case "$*" in
    -h\ *|--help\ *|-V|--version)
      # A request for help or version are special cases.
      exec /usr/sbin/emailrelay $@ ;;
    -*)
      # If the arguments (CMD, assuming we're an ENTRYPOINT) starts
      # with a minus-dash, it's the options to emailrelay.
      # Prefill some defaults (so we don't have to specify them),
      # then run.
      exec /usr/sbin/emailrelay $DEFAULT_OPTS $@ ;;
    *)
      # If arguments don't start with a minus-dash, let's assume
      # it's a proper shell command to execute and do so.
      exec "$@" ;;
esac
