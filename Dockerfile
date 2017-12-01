FROM alpine:latest
LABEL maintainer="Aleksei Zhukov <drdaeman@drdaeman.pp.ru>"

RUN echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
 && apk add --no-cache libstdc++ openssl ca-certificates dumb-init swaks@testing perl-net-ssleay \
 && update-ca-certificates

ARG DOWNLOAD_URL=https://downloads.sourceforge.net/project/emailrelay/emailrelay/1.9/emailrelay-1.9-src.tar.gz

RUN apk add --no-cache --virtual .deps curl g++ make autoconf automake openssl-dev \
 && mkdir -p /tmp/build && cd /tmp/build \
 && curl -o emailrelay.tar.gz -L "${DOWNLOAD_URL}" \
 && tar xzf emailrelay.tar.gz \
 && cd emailrelay-1.9 \
 && ./configure --prefix=/usr --with-openssl \
 && make \
 && make install \
 && apk --no-cache del .deps \
 && cd / \
 && rm -rf /tmp/build /var/tmp/* /var/cache/apk/* /var/cache/distfiles/* \
 && mkdir -p /var/spool/emailrelay

ENV PORT=587
COPY run.sh /run.sh

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/run.sh"]
CMD []

ENV SWAKS_OPTS="-tls"
HEALTHCHECK --interval=2m --timeout=5s \
  CMD swaks -S -h localhost -s localhost:${PORT:-587} -q HELO ${SWAKS_OPTS} || exit 1
