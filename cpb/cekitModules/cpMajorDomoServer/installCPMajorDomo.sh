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

# pip install ./cpMajorDomo

# useful while developing majorDomo

cat << EOF > installEditableMajorDomo

pip install pdm

echo "export PATH=$HOME/.local/bin:$PATH" >> $HOME/.bashrc
pdm --pep582 bash                         >> $HOME/.bashrc

echo "export PATH=$HOME/.local/bin:$PATH" >> $HOME/.ashrc
pdm --pep582 bash                         >> $HOME/.ashrc

source .bashrc

cd /root/majorDomo

pdm install

./scripts/installEditableCpmdCommand

cd /root/majorDomo/__pypackages__/3.10/lib

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

