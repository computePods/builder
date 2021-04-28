#!/bin/sh

# This shell script installs the computePods cpPyNatsFastAPI tools

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

pip3 install setuptools wheel
pip3 install aiofiles
pip3 install asyncio-nats-client
pip3 install fastapi
pip3 install hypercorn
