#!/bin/sh

# This shell script installs the computePods MajorDomo tool

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

################################################
# install cpMajroDomo application
# see: https://github.com/computePods/computePodMajorDomo
#

unpackArtifact () {
  cd
  mkdir -p ${1}
  tar xvf /tmp/artifacts/${1}.tar.gz --directory ${1} --strip-components=1
}

unpackArtifact cpMajorDomo
