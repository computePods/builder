#!/bin/sh

# This shell script builds the syncThingServer

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

go version

cd

git clone https://github.com/syncthing/syncthing.git

cd syncthing

go run build.go

cd bin

ls -la

