#!/bin/sh

# This shell script install the base debian system

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

cp /tmp/artifacts/syncthing /usr/local/bin

mkdir -p /root/.config/syncthing
cp /tmp/artifacts/config.xml /root/.config/syncthing
