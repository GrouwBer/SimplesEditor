FROM debian:12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      qemu-user-static \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -u 65534 -M -s /usr/sbin/nologin sandbox || true

USER 65534:65534
WORKDIR /sandbox
