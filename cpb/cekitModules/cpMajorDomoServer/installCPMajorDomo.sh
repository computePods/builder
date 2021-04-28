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
cd
mkdir -p cpMajorDomo
tar xvf /tmp/artifacts/cpMajorDomo.tar.gz --directory cpMajorDomo --strip-components=1
#cp -r ${1}/${2} /usr/local/share/lua/5.4/${3}
#unpackArtifact cpMajorDomo cpMajorDomo

