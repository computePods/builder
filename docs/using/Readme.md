# Using the Compute Pods system

A running Compute Pods system is a loose federation of individual Compute 
Pods one on each of a number of computers. These computers can be 
dedicated servers, Kubernetes nodes, or they could be "desktops" some of 
whose compute cycles are being contributed by their individual users. All 
of these computers *must* be connected by a network via either a private 
local area network, a virtual private network, or the greater Internet. 
All of these computers *must* allow TCP traffic through their firewalls on 
a small number of control ports. 

Setting up a federation of Compute Pods consists of a number of steps.

1. [Describe the overall system.](describeSystem.md)

2. [Build the Containers required by the system.](buildContainers.md) 

3. [Deploy a Compute Pod to one or more computers in the 
   system.](deployComputePod.md) 

