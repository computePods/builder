#!/bin/sh

# This shell script installs the computePods Chef tool

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

# Install the binary lua luv-Nats and WebLit modules from the artifact image
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
# install cpChef application
#
#unpackArtifact cpChef cpChef
