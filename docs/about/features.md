# Features

## 1. "C2 framework"
At its core, Consortium is a _C2 framework_. For the uninitiated (if so, welcome!), a C2
framework is a set of tools or software used by adversaries (hackers, pen-testers, state sponsored entities) to
maintain control over a remote system they already have initial access to.

As a framework, Consortium provides users with a set of software tools that makes it
very easy to write custom listeners and agents that can just "plug in" to the system. It
takes away all the finicky stuff you have to worry about when writing custom pieces of
malware such as task tracking, jobs management, session sharing, etc. This lets you
focus on the fun part: writing malware.

Of course Consortium is not _just_ a set of software tools. It comes shipped with its
own listener and agent implementations that can be used out of the box. So you could
think of it as a C2 _application_ that is built on top of an underlying
_software framework_.

## 2. "Programming language agnostic, and networking protocol agnostic"
**Networking protocol agnostic** - As a software framework, Consortium imposes no
limitations on the types of listeners and agents that can be used. This means that
listeners and agents can be used in the framework that communicate over any networking
protocol, regardless of the model or method of communication.

**Programming language agnostic** - Consortium is written entirely in Python so it
provides a Python based software framework you can build off of. However, the design of
the framework allows you to remotely hook in listeners and agents written in any
arbitrary language to the framework over its server's API.

## 3. "Designed to be collaborative, highly extensible, and modular"
**Collaborative** - Consortium adopts a server-client model to allow collaboration.
The server manages all C2 related activities while multiple clients can simply connect
to the same server to perform C2 related operations together.

**Extensible** - The Consortium server exposes a REST API for most C2 related
functionality. A websockets API is additionally provided to allow for server-pushed
events to be received. Having a common API means that it is possible to write software
to extend the framework's capabilities. You can automate actions, write custom hooks,
and even develop your own custom client based off the API alone.

**Modular** - The Consortium
