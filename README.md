# Docker image for E-MailRelay ([dcagatay/emailrelay](https://hub.docker.com/r/dcagatay/emailrelay))

[![Docker Pulls](https://img.shields.io/docker/pulls/dcagatay/emailrelay)](https://hub.docker.com/r/dcagatay/emailrelay)
[![GitHub tag](https://img.shields.io/github/v/tag/dogukancagatay/docker-emailrelay)](https://github.com/dogukancagatay/docker-emailrelay/tags)

Available Tags:

[List of all image tags](https://hub.docker.com/r/dcagatay/emailrelay/tags)

- `latest`, `2.6`
- `2.5.2`
- `2.5.1a`
- `2.5.1`
- `2.5`
- `2.4.1`
- `2.4`
- `2.3`

Alpine based Docker image for E-MailRelay. You can find more on its [website](http://emailrelay.sourceforge.net).

Container configuration is done via _environment variables_ and _command line arguments_. Command line arguments are given directly to `emailrelay` executable.

To see all command line options of `emailrelay` command:

```bash
docker run --rm dcagatay/emailrelay --help --verbose
```

## Usage

Some usage examples are given in `docker-compose.yml`.

### Example Usage with for Gmail SMTP Service

Sample configuration for sending emails from your Gmail account.

Add your credentials to `client-auth.txt`.

```
client plain example@gmail.com gmail-or-app-password
```

Run the docker container

```bash
docker run --rm \
  -p "25:25" \
  -v "$PWD/client-auth.txt:/client-auth.txt" \
  dcagatay/emailrelay --forward-on-disconnect --forward-to smtp.gmail.com:587 --client-tls --client-auth=/client-auth.txt
```

## Environment Variables

### `DEFAULT_OPTS`

By default the following arguments are given on runtime. You can overwrite `DEFAULT_OPTS` environment variable to change or disable this behaviour.

```text
--no-daemon --no-syslog --log --log-time --remote-clients
```

### `PORT`

The port that E-MailRelay runs on. Default value is `25`. If you did TLS configuration you need to set this variable to `587` or something else.

### `SPOOL_DIR`

Spool directory for E-MailRelay. No need to change. Default value: `/var/spool/emailrelay`

### `SWAKS_OPTS`

This variable is used to give options to _swaks_, it is used on built-in health-check functionality. If you serve with TLS configuration you need to set this variable to `-tls`. Default value: _empty-string_

## Filter Scripts, Client/Server Authentication, and Others

Inside `config` directory you will find sample files for usage with filter functionality, SMTP client authentication and relay server authentication.

For any further configuration or details, refer to the [E-MailRelay documentation](http://emailrelay.sourceforge.net).

## Testing

You can test your configuration with _swaks_.

```bash
echo "This is a test message." | swaks --to to@mail.dev --from from@mail.dev --server emailrelay --port 9025
```

Or use a container, after running the containers in `docker-compose.yml` you could run the following command to test with _swaks_ and see the test email on [localhost:8025]().

```bash
docker-compose run \
  --entrypoint /bin/sh \
  emailrelay \
  -c 'echo "This is a test message." | swaks --to <to@mail.dev> --from <from@mail.dev> --server emailrelay --port 25'
```

## Additions to `drdaeman/docker-emailrelay`

- E-MailRelay version upgrade(s).
- Smaller container images.
- Included `bash` shell for further scripting.
- Default TLS configuration is changed to insecure configuration.
- Sample files for advanced configuration.
