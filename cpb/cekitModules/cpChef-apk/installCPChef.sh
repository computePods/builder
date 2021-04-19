#!/bin/sh

# This shell script installs the computePods Chef tool

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

################################################
# Install the binary lua modules from the build phase
#
cd 
tar xvf /tmp/artifacts/luaLibs.tar --directory /

################################################
# install lua uuid
#
cd
mkdir -p luaUUID
tar xvf /tmp/artifacts/luaUUID.tar.gz --directory luaUUID --strip-components=1
cp luaUUID/src/uuid.lua /usr/local/share/lua/5.4

################################################
# install lua NATS
#
cd
mkdir -p luaNATS
tar xvf /tmp/artifacts/luaNATS.tar.gz --directory luaNATS --strip-components=1
cp luaNATS/src/nats.lua /usr/local/share/lua/5.4

################################################
# install lua yaml
#
cd
mkdir -p luaYAML
tar xvf /tmp/artifacts/luaYAML.tar.gz --directory luaYAML --strip-components=1
cp luaYAML/yaml.lua /usr/local/share/lua/5.4

################################################
# install lua pprint
#
cd
mkdir -p luaPPrint
tar xvf /tmp/artifacts/luaPPrint.tar.gz --directory luaPPrint --strip-components=1
cp luaPPrint/pprint.lua /usr/local/share/lua/5.4
