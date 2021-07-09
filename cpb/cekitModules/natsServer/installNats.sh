#!/bin/sh

# This shell script installs that NATS messaging server.

# This is based upon the Alpine Dockerfile at:
#   https://github.com/nats-io/nats-docker/tree/master/2.2.1


echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

set -eux

NATS_SERVER={{ versions.natsServer.version }}

apkArch="$(apk --print-arch)"

case "$apkArch" in
  aarch64) natsArch='arm64'; sha256='{{ versions.natsServer.sha256.arm64 }}' ;;
  armhf) natsArch='arm6'; sha256='{{ versions. natsServer.sha256.arm6 }}' ;;
  armv7) natsArch='arm7'; sha256='{{ versions.natsServer.sha256.arm7 }}' ;;
  x86_64) natsArch='amd64'; sha256='{{ versions.natsServer.sha256.amd64 }}' ;;
  x86) natsArch='386'; sha256='{{ versions.natsServer.sha256.i386 }}' ;;
  *) echo >&2 "error: $apkArch is not supported!"; exit 1 ;;
esac

wget -O nats-server.zip "https://github.com/nats-io/nats-server/releases/download/v${NATS_SERVER}/nats-server-v${NATS_SERVER}-linux-${natsArch}.zip"

echo "${sha256} *nats-server.zip" | sha256sum -c -

apk add --no-cache ca-certificates
apk add --no-cache --virtual buildtmp unzip

unzip nats-server.zip "nats-server-v${NATS_SERVER}-linux-${natsArch}/nats-server"
rm nats-server.zip
mv "nats-server-v${NATS_SERVER}-linux-${natsArch}/nats-server" /usr/local/bin
rmdir "nats-server-v${NATS_SERVER}-linux-${natsArch}"

apk del --no-cache --no-network buildtmp
