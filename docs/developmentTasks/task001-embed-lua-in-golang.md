# Provide project interface to an embeded Lua instance inside GoLang

- **Started**: 2021-03-03
- **(Essentially) Completed**: 2021-03-03

## Goal

We want to use [Lua](https://www.lua.org/) (version 5.4) as a simple 
configuraiton/scripting langage inside most of our GoLang based tools. 

## Solution

We will use our own [diSimplex fork of 
golua](https://github.com/diSimplex/golua). This fork contains minor 
updates to make it compatible with Lua 5.4 on linux machines. The original 
[golua can be found here](https://github.com/aarzilli/golua). 

## Problems

1. At the moment there does not seem to be a `ToInteger` or `ToFloat` 
   method in goLua. (Lua 5.1 forced all numbers as Integers, sometime 
   before Lua 5.4 floats were added). We may need to fork goLua to 
   explicitly add number handling. 

2. Line 22 in the file `lua/lua.go` defines the `cgo` LDFLAGS for the 
   `lua54` compile tag (for Lua 5.4). Unfortunately we need to explicitly 
   add a `-ldl` to the existing LDFLAGS. 

## Questions

1. **Q**: How do we map Lua values to Go values?

   **A**: We can use goLua's standard stack mechanism and the associated 
   `IsXXX`/`PushXXX`/`ToXXX` methods. We can also consider using either
   of the [Luar](https://github.com/stevedonovan/luar/) or
   [lunatico](https://github.com/fiatjaf/lunatico) reflection mechanisms.

2. **Q**: Should we link against a shared or statically built Lua library?

   If the *only* version of the Lua library is statically built, then 
   `cgo` successfully links this version (but the LDFLAGS do need the 
   additional `-ldl` flag, since Lua 5.4 now allows dynamic libraries). 

   If both the static and the shared Lua libraries are pressent, I suspect 
   `cgo` is linking the shared version in preference to the static 
   version. 

   *SO* this is really a question of how we want to build and distribute 
   the Lua 5.4 libraries in the containers. This might be very important 
   for any use of the Alpine based containers. 

   This is also a question for building and distributing the assembly 
   tools. In particular if we link to the static library, how do we 
   distribute any pure Lua scripts? 
   
## Resources

- [Lua 5.4 documentation](https://www.lua.org/manual/5.4/)

- [golua](https://github.com/aarzilli/golua)
