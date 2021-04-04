# Compute Pods

A tool to build distributed peer-to-peer pods of compute modules for 
embarrassingly parallel problems using rootless Podman containers. 

## Overall architecture

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
