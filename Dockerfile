FROM alpine:3.20

# BASE_VERSION is X.X for minor and X.X.X for patch
ARG BASE_VERSION=2.6
ARG SUB_VERSION=
ARG DOWNLOAD_URL=https://downloads.sourceforge.net/project/emailrelay/emailrelay/${BASE_VERSION}/emailrelay-${BASE_VERSION}${SUB_VERSION}-src.tar.gz

LABEL org.opencontainers.image.title="E-MailRelay"
LABEL org.opencontainers.image.description="Alpine based container image for E-mailRelay"
LABEL org.opencontainers.image.source="https://github.com/dogukancagatay/docker-emailrelay"
LABEL org.opencontainers.image.licenses=MIT
LABEL org.opencontainers.image.authors="Dogukan Cagatay <dcagatay@gmail.com>"
LABEL org.opencontainers.image.version=${BASE_VERSION}${SUB_VERSION}

ENV PORT="25" \
    SWAKS_OPTS="" \
    DEFAULT_OPTS="--no-daemon --no-syslog --log --log-time --remote-clients" \
    SPOOL_DIR="/var/spool/emailrelay"

RUN apk --update-cache add --virtual build-dependencies build-base curl g++ make autoconf automake openssl-dev \
    && mkdir -p /tmp/build \
    && cd /tmp/build \
    && curl -o emailrelay.tar.gz -L "${DOWNLOAD_URL}" \
    && tar xzf emailrelay.tar.gz \
    && cd emailrelay-* \
    && ./configure --prefix=/app --with-openssl \
    && make -j $(nproc --all) \
    && make install \
    && rm -rf /tmp/build \
    && apk del build-dependencies

RUN apk add --update --no-cache \
    libstdc++ \
    openssl \
    ca-certificates \
    dumb-init \
    bash \
    perl-net-ssleay && \
    apk add --update --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    swaks \
    && rm -rf /var/tmp/* /var/cache/apk/* /var/cache/distfiles/* \
    && mkdir -p "${SPOOL_DIR}"

COPY run.sh /run.sh

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/run.sh"]
CMD []

HEALTHCHECK --interval=2m --timeout=5s \
    CMD swaks -S -h localhost -s localhost:${PORT} -q HELO ${SWAKS_OPTS} || exit 1
