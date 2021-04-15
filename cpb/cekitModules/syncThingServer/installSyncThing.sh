#!/bin/sh

# This shell script install the base debian system

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

mkdir -p $HOME/bin

export PATH=/commons/bin:$HOME/bin:$PATH

mkdir -p /usr/local/bin

# record the pde variables
#
export PDE_VARS=$HOME/pdeVars
#
rm -rf $PDE_VARS
cat <<PDE_FUNCTIONS > $PDE_VARS
set -e
set +x
#
# This pde bash function records an environment variable in the 
# \$PDE_VARS file.
#
recordVar() {
  varName=\$1
  shift
  echo "export \$varName=\"\$*\"" >> \$PDE_VARS
  echo "export \$varName=\"\$*\""
  . \$PDE_VARS
}
#
# This pde bash function records an comment in the 
# \$PDE_VARS file.
#
recordComment() {
  echo "# \$*" >> \$PDE_VARS
}
PDE_FUNCTIONS

. $PDE_VARS

recordVar PDE_VARS $HOME/pdeVars

echo "source $HOME/pdeVars" >> $HOME/.bashrc

touch $HOME/finalizePDE
