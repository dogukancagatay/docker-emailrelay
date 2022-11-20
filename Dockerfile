FROM alpine:3.16 as builder
ARG BASE_VERSION=2.4

ARG DOWNLOAD_URL=https://downloads.sourceforge.net/project/emailrelay/emailrelay/${BASE_VERSION}/emailrelay-${BASE_VERSION}-src.tar.gz

RUN apk add --no-cache curl g++ make autoconf automake openssl-dev \
    && mkdir -p /tmp/build && cd /tmp/build \
    && curl -o emailrelay.tar.gz -L "${DOWNLOAD_URL}" \
    && tar xzf emailrelay.tar.gz \
    && cd emailrelay-* \
    && ./configure --prefix=/app --with-openssl \
    && make -j $(nproc --all) \
    && make install

FROM alpine:3.16
LABEL maintainer="Dogukan Cagatay <dcagatay@gmail.com>"

ENV PORT="25" \
    SWAKS_OPTS="" \
    DEFAULT_OPTS="--no-daemon --no-syslog --log --log-time --remote-clients" \
    SPOOL_DIR="/var/spool/emailrelay"

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
COPY --from=builder /app /app

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/run.sh"]
CMD []

HEALTHCHECK --interval=2m --timeout=5s \
    CMD swaks -S -h localhost -s localhost:${PORT} -q HELO ${SWAKS_OPTS} || exit 1
