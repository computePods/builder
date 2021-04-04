# Describing the overall Compute Pods system

The Compute Pods communicate via TLS which is secured at both ends using a 
client/server certificate. Each individual Compute Pod is assigned its own 
client/server certificate. To be able to do this, each Compute Pod needs 
to be described before being deployed. 

Similarly each Compute Pod requires a number of different TCP ports for 
communication between pods. Since Compute Pods are meant to be run-able on 
various compute platforms (including "desktops"), there is a potential for 
these TCP ports to assigned to other tasks. This means that all of these 
communications ports *must* be configurable. 

Similarly each Compute Pod requires a *host* directory in which to 
synchronize files between the pods. 

Similarly each *user* requires their own *client* certificate.

Since we will be issuing certificates, we need to define the (private) 
Certificate Auhority which will issue these certificates. 
