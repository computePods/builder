# Overall architecture

A ComputePods "pod" is an coordinated collection of
[OCI Container](https://opencontainers.org/) containers.
These ComputePods pods can be run rootless using [Podman](https://podman.io/)
[Pod](http://docs.podman.io/en/latest/pod.html) (on a 
private collection of computers to which a user has access)
or as a [Kubernetes](https://kubernetes.io/)
[Pod](https://kubernetes.io/docs/concepts/workloads/pods/)
(in a more specialized production environment).

Each pod consists of:

- A [NATS](https://nats.io/) container used to provide inter/intra pod
  communication.

- A [Syncthing](https://syncthing.net/) container used to syncronize files
  between pods.

- A collection of different "worker" containers, one or more for each 
  computational task. These worker containers consist a GoLang controler 
  process which forks "tasks" consisting of any containerizable 
  compuational "command line" process. 

This simple architecture is sufficent to parallelize any 
[embarasingly parallelizable](https://en.wikipedia.org/wiki/Embarrassingly_parallel)
computational task (such as, but not limited to, compilation of source code).

Suitably programmed computational tasks can interact with the NATS 
"back-plane" to initiate, and wait for sub-tasks to be run. Similarly, 
suitably programmed tasks can interact with the Syncthing "back-plane" to 
ensure all required files are syncronized between workers potentially 
contained in pods on different computers. 

## Security

All data flows between pods and the containers inside pods will be done 
using double-ended [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security).

This means that all pods (and end-users) are assigned individual TLS 
certificates and all connections require TLS certificates from both the 
"server" and the "client". 

This security regime *should* work in both the Podman (tested) and 
Kubernetes (untested) environments. 
