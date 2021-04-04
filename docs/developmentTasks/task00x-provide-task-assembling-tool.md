# Provide a tool to assemble container images for worker tasks

- **Started**: not yet begun

## Goal

We want a tool which reads a Lua configuration file and builds a container.

This tool will probably make use of one or more templating systems to 
generate the required container build files. (Among many other tasks).

## Solution


## Subtasks

1. Skectch build of NATS container
2. Skectch build of Syncthing container
3. Skectch build of GCC container

## Problems

1. We are not sure what platforms these tools will be used on... will we 
   have access to POSXI shell scripting? 

## Questions

1. **Q**: Should we use Buildah libraries to directly construct containers?

   **A**: No.

   We might consider this *if* the buildah project provided a 
   stable GoLang API. However the current buildah project only provides a 
   stable command-line interface.

   (The [Open Repository fo Container Tools](https://github.com/containers)
   does provide GoLang APIs but they look more complex than we want to use). 

   Instead we should simply use Podman's (or Docker's) dockerfile system 
   to build our containers, since podman (or podman/kubernetes, or 
   docker/kubernetes) is already a runtime dependency. Using dockerfiles 
   also makes sense since they are so well known and have many examplars 
   from which to base new variants required for a given task worker. 

2. **Q**: What directory structure should we use to contain the 
   (potentially) multiple artefacts required to build a single container. 

## Resources

### Buildah libraries

- [Buildah](https://buildah.io/)

- [Buildah Blogs](https://buildah.io/blogs/)

- [Buildah Tutorials](https://github.com/containers/buildah/tree/master/docs/tutorials)

- [Include Buildah in your build tool](https://github.com/containers/buildah/blob/master/docs/tutorials/04-include-in-your-build-tool.md)

- [Building with Buildah: Dockerfiles, command line, or scripts](https://www.redhat.com/sysadmin/building-buildah)

### GoLang Templating

- [tex/template](https://golang.org/pkg/text/template/)

### Lua Templating

- [Using Lua as a Templating Engine](https://nachtimwald.com/2014/08/06/using-lua-as-a-templating-engine/)

- [Lua Template Engine Revisited])(https://nachtimwald.com/2015/05/07/lua-template-engine-revisited/)

- [Introducing Lua Templates](http://lua.space/webdev/introducing-lua-templates)

- [arcapos/luatemplate](https://github.com/arcapos/luatemplate) (most 
  active GitHub project; last changed 2 months ago; documented in the blog 
  listed above). 

- [bungle/lua-resty-template](https://github.com/bungle/lua-resty-template) 
  (last changed 5 months ago; reasonably well documented) 

- [dannote/lua-template](https://github.com/dannote/lua-template/) (oldest 
  GitHub project; last changed 2 years ago; very small code base but 
  allows external sub-templates) 
