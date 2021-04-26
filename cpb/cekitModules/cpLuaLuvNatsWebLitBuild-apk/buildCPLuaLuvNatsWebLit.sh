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

getGitPackage () {
  cd
  git clone https://github.com/${1}/${2}.git $3
  cd $2
}

cpPureLuaPackage () {
  cp -R $1 /usr/local/share/lua/5.4/${2}
}

############################################################################
# We start by compiling all of the lua packages with C code
############################################################################

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
#
getGitPackage mpx lua-cjson
git checkout $luaCJsonVersion
make LUA_VERSION=5.4 -j $numCores
make LUA_VERSION=5.4 install
make LUA_VERSION=5.4 install-extra

################################################
# Build luv
# See; https://github.com/luvit/luv
#
getGitPackage luvit luv --recursive
export LUA_BUILD_TYPE=System
export WITH_LUA_ENGINE=Lua
make -j $numCores
make install

################################################
# Build lua-openssl
# See; https://github.com/zhaozg/lua-openssl
#
getGitPackage zhaozg lua-openssl --recursive
make -j $numCores
make install

############################################################################
# Now we simply copy the PURE lua packages
############################################################################

################################################
# Insall UUID
# See; https://github.com/Tieske/uuid
#
getGitPackage Tieske uuid
cpPureLuaPackage src/uuid.lua

################################################
# Insall lua-yaml
# See; https://github.com/exosite/lua-yaml
#
getGitPackage exosite lua-yaml
cpPureLuaPackage yaml.lua

################################################
# Insall pprint
# See; https://github.com/jagt/pprint.lua
#
getGitPackage jagt pprint
cpPureLuaPackage pprint.lua

################################################
# Insall luv-nats
# See; https://github.com/computePods/luv-nats
#
getGitPackage computePods luv-nats
cpPureLuaPackage src/nats.lua 

################################################
# Insall webLit
# See; https://github.com/creationix/weblit
#
getGitPackage creationix weblit
cpPureLuaPackage libs

################################################
# Insall coro-http-luv
# See; https://github.com/squeek502/coro-http-luv
#
getGitPackage squeek502 coro-http-luv
cpPureLuaPackage coro-http-luv

############################################################################
# now we make a tar file of the lua libraries 
############################################################################
#
cd
tar cvf luaLibs.tar /usr/local/include/lua* /usr/local/bin /usr/local/lib /usr/local/share
