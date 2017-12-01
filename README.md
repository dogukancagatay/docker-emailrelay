Docker image for E-MailRelay
============================

Usage example:

    docker run --name emailrelay \
      -v /etc/ssl/private/key_and_cert.pem:/etc/ssl/server.pem:ro \
      drdaeman/emailrelay \
      -D msa.example.com --immediate --forward-to mail.example.org:smtp \
      --server-tls /etc/ssl/server.pem --client-tls

To get help, check emailrelay documentation or use:

    docker run --rm drdaeman/emailrelay --help

Note, the `--remote-clients --port $PORT` (and some more) options are
passed automatically, so to change client port just redefine the `PORT`
environment variable. The default port number is 587.

For a full control, run a full command starting with `emailrelay`, i.e.:

    docker run drdaeman/emailrelay emailrelay --help
