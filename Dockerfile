FROM python:alpine

ENV SHELL /bin/sh
ENV CC /usr/bin/clang
ENV CXX /usr/bin/clang++
ENV LANG C.UTF-8

ENV PYTHONUNBUFFERED 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_NO_CACHE_DIR 0

WORKDIR /srv
COPY requirements.txt /srv

RUN \
# Install development tools
    apk add --virtual .dev-deps clang g++ linux-headers \
    && addgroup -S oauth \
    && adduser -S oauth -G oauth \
    && chown -R oauth:oauth /srv \
    && pip install -U --no-cache-dir -r requirements.txt \
# Cleanup
    && apk del .dev-deps \
    && rm -rf /tmp/* /var/cache/apk/*

COPY . /srv

USER oauth
ENTRYPOINT ["uwsgi", "--ini", "wsgi.ini"]
