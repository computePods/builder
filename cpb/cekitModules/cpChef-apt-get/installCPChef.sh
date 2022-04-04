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
}

################################################
# install cpChef application
#
unpackArtifact cpChef

# pip install ./cpChef

# useful while developing chef

cat << EOF > installEditableChef

pip install pdm

echo "export PATH=$HOME/.local/bin:$PATH" >> $HOME/.bashrc
pdm --pep582 bash                         >> $HOME/.bashrc

echo "export PATH=$HOME/.local/bin:$PATH" >> $HOME/.ashrc
pdm --pep582 bash                         >> $HOME/.ashrc

source .bashrc

cd /root/chef

pdm install

./scripts/installEditableCpchefCommand

cd /root/chef/__pypackages__/3.10/lib

if [ ! -L cpinterfaces ] ; then
  mv cpinterfaces cpinterfaces.static
  ln -s /cpinterfaces .
fi

if [ ! -L cputils ] ; then
  mv cputils cputils.static
  ln -s /cputils .
fi

cd

EOF
