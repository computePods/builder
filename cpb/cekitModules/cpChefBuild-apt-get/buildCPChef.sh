#!/bin/sh

# This shell script builds the computePods Chef tool
#
# In this script we ONLY worry about the Lua modules that have C 
# components which need compilation. 
#

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

################################################
# Versions
#
luaVersion=5.4.2
luaCJsonVersion=e8972ac

numCores=$(nproc)

################################################
# Build lua
# See; https://www.lua.org/download.html
#
cd
wget http://www.lua.org/ftp/lua-$luaVersion.tar.gz
mkdir lua
tar xvf lua-$luaVersion.tar.gz --directory=lua --strip-components=1
cd lua
make -j $numCores
make install

# Install our version of the pgk-config file for Lua
# This is required by both luv and lua-openssl
#
mkdir -p /usr/local/lib/pkgconfig
cp /tmp/artifacts/lua.pc /usr/local/lib/pkgconfig

################################################
# Build lua-cjson
# See; https://github.com/mpx/lua-cjson
cd
git clone https://github.com/mpx/lua-cjson.git
cd lua-cjson
git checkout $luaCJsonVersion
make LUA_VERSION=5.4 -j $numCores
make LUA_VERSION=5.4 install
make LUA_VERSION=5.4 install-extra

################################################
# Build luv
# See; https://github.com/luvit/luv
#
cd
git clone https://github.com/luvit/luv.git --recursive
cd luv
export LUA_BUILD_TYPE=System
export WITH_LUA_ENGINE=Lua
make -j $numCores
make install

################################################
# Build lua-openssl
# See; https://github.com/zhaozg/lua-openssl
#
cd
git clone https://github.com/zhaozg/lua-openssl.git --recursive
cd lua-openssl
make -j $numCores
make install

################################################
# make a tar file of the lua libraries 
#
cd
tar cvf luaLibs.tar /usr/local/include/lua* /usr/local/bin /usr/local/lib /usr/local/share
