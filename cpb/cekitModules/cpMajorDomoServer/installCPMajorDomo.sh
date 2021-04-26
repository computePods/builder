#!/bin/sh

# This shell script installs the computePods MajorDomo tool

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

#pip install asyncio-nats-client
###pip install asynchttp
### OR
#pip install fastapi
#pip install uvicorn
### OR
###pip install hypercorn
## 76MB
#
##gem install nats
##gem install thin
##gem install sinatra
##gem install async_sinatra
## 224MB (but this includes gcc and friends)

################################################
# Install the binary lua modules from the build phase
#
cd 
tar xvf /tmp/artifacts/luaLibs.tar --directory /

unpackArtifact () {
  cd
  mkdir -p ${1}
  tar xvf /tmp/artifacts/${1}.tar.gz --directory ${1} --strip-components=1
  cp -r ${1}/${2} /usr/local/share/lua/5.4/${3}
}

################################################
# install cpMajroDomo application
#
#unpackArtifact cpMajorDomo cpMajorDomo

