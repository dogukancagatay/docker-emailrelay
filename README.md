# Docker image for E-MailRelay

![MicroBadger Size](https://img.shields.io/microbadger/image-size/dcagatay/emailrelay)
![MicroBadger Layers](https://img.shields.io/microbadger/layers/dcagatay/emailrelay)
![Docker Pulls](https://img.shields.io/docker/pulls/dcagatay/emailrelay)
![Docker Stars](https://img.shields.io/docker/stars/dcagatay/emailrelay)

Available Tags:

- [latest](https://github.com/dogukancagatay/docker-emailrelay/blob/master/Dockerfile)
- [2.4](https://github.com/dogukancagatay/docker-emailrelay/blob/2.4/Dockerfile)
- [2.3](https://github.com/dogukancagatay/docker-emailrelay/blob/2.3/Dockerfile)
- [2.2](https://github.com/dogukancagatay/docker-emailrelay/blob/2.2/Dockerfile)
- [2.1](https://github.com/dogukancagatay/docker-emailrelay/blob/2.1/Dockerfile)
- [2.0.1](https://github.com/dogukancagatay/docker-emailrelay/blob/2.0.1/Dockerfile)

Alpine based Docker image for E-MailRelay. You can read capabilities, configuration etc. of E-MailRelay on its [website](http://emailrelay.sourceforge.net).

Container configuration is done via _environment variables_ and _command line arguments_. Command line arguments are given directly to `emailrelay` executable.

To see all command line options of `emailrelay` command:

```bash
docker run --rm dcagatay/emailrelay --help --verbose
```

## Usage

Some usage examples are given in `docker-compose.yml`.

#### Example Usage with for Gmail SMTP Service

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

#### `DEFAULT_OPTS`

By default the following arguments are given on runtime. You can overwrite `DEFAULT_OPTS` environment variable to change or disable this behaviour.

```
--no-daemon --no-syslog --log --log-time --remote-clients
```

#### `PORT`

The port that E-MailRelay runs on. Default value is `25`. If you did TLS configuration you need to set this variable to `587` or something else.

#### `SPOOL_DIR`

Spool directory for E-MailRelay. No need to change. Default value: `/var/spool/emailrelay`

#### `SWAKS_OPTS`

This variable is used to give options to _swaks_, it is used on built-in health-check functionality. If you serve with TLS configuration you need to set this variable to `-tls`. Default value: _empty-string_

## Filter Scripts, Client/Server Authentication, and Others

Inside `config` directory you will find sample files for usage with filter functionality, SMTP client authentication and relay server authentication.

For any further configuration or details, refer to the [E-MailRelay documentation](http://emailrelay.sourceforge.net).

## Testing

You can test your configuration with _swaks_.

```bash
docker run --rm \
  flowman/swaks \
  echo "This is a test message." | swaks --to to@mail.dev --from from@mail.dev --server localhost --port 25
```

## Additions to `drdaeman/docker-emailrelay`

- E-MailRelay version upgrade.
- Multi stage build for quicker builds.
- `bash` shell in included for further scripting.
- Default TLS configuration is changed to insecure configuration.
- Sample files for advanced configuration.
