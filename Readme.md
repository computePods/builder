# Compute Pods build tool

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
(in a more specialised production environment).

Each pod consists of:

- A [NATS](https://nats.io/) container used to provide inter/intra pod
  communication.

- A ComputePod MajorDomo container which manages the computation processes.

- A collection of different "worker" containers, one or more for each
  computational task. These worker containers consist a Python controller
  process which forks "tasks" consisting of any containerizable
  computational "command line" process.

This simple architecture is sufficient to parallelize any
[embarrassingly parallelizable](https://en.wikipedia.org/wiki/Embarrassingly_parallel)
computational task (such as, but not limited to, compilation of source code).

Suitably programmed computational tasks can interact with the NATS
"back-plane" to initiate, and wait for sub-tasks to be run.

## This ComputePods build tool

This ComputePods build tool takes a description of the different pods
required to solve a given problem and using [Cekit](https://cekit.io/)
configures and builds the required Podman container images.

## Installation

The build tool is a python command. As such it can be installed using
[pip](https://pip.pypa.io/en/stable/),
[pipx](https://pypa.github.io/pipx/), or, for a fully editable development
version, using [PDM](https://pdm.fming.dev/)).

At the moment the ComputePods build tool is *not* on [pypi.org](pypi.org)
so you will need to use one of the following ways to install it:

1. **using pip**:

   ```
   pip install --user git+https://github.com/computePods/computePodBuilder.git
   ```

2. **using pipx**:

   ```
   pipx install git+https://github.com/computePods/computePodBuilder.git
   ```

3. **using pdm**: is slightly more involved, however it is required if you
   want to develop your own version.

   ```
   git clone https://github.com/computePods/computePodBuilder.git
   cd computePodBuilder
   pdm install
   ./scripts/installEditableCpbCommand
   ```

   We use the PDM Python development manager, to manage the ComputePods
   builder's Python dependencies in a "node_modules" like way. This allows
   you to keep the build tool's dependencies cleanly separate from the
   dependencies of any other Python tool you might be using.

### External requirements

The ComputePods build tool makes use of the [Cekit](https://cekit.io/)
tool as an *external* dependency (that is, the `cekit` command must be
located in your `$PATH`). Again, you can use either `pip`, or `pipx` to
install it on your machine.

- **using pip**:

  ```
  pip install --user cekit
  ```

- **using pipx**:

  ```
  pipx install cekit
  ```

**NOTE:** on a [Debian](https://www.debian.org/) based distribution, such
as, for example, [Ubuntu](https://ubuntu.com/), you *may* need to install
the [odcs](https://pypi.org/project/odcs/) client library as a separate
step.

- **using pip**:

  ```
  pip install --user odcs
  ```

- **using pipx**:

  ```
  pipx runpip cekit install odcs
  ```

  (This will install the odcs Python *library*, in pipx's Cekit virtual
  environment -- which ensures the odcs library will be cleanly removed if
  and when you uninstall Cekit itself).