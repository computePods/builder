#!/bin/sh

# This shell script installs the computePods Chef tool

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

cd

# We need to upgrade to the most recent version of pip to allow the 
# cryptographic package to be installed without requiring the Rust 
# compiler. 
#
python3 -m pip install --upgrade pip

# We need the setuptools python package to manage our computePodChef
#
python3 -m pip install --upgrade setuptools

# We need the wheel python package to manager the dependencies
#
python3 -m pip install --upgrade wheel 

python3 -m pip list

git clone https://github.com/computePods/computePodChef.git

# pip3 install --editable /root/computePodChef
