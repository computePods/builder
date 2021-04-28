#!/bin/sh

# This shell script installs the computePods cpPyNatsFastAPI tools

echo "----------------------------------------------------------------------"
echo $0
echo "----------------------------------------------------------------------"
echo ""

pip install aiofiles
pip install asyncio-nats-client
pip install fastapi
pip install hypercorn
