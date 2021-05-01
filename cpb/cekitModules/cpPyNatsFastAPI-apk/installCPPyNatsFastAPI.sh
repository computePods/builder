#!/bin/sh

# This shell script installs the computePods cpPyNatsFastAPI tools

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

pip install networkx
pip install pyyaml
pip install aiofiles
pip install asyncio-nats-client
pip install fastapi
pip install hypercorn
