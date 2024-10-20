# Consortium
Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _collaborative_, 
_highly extensible_, and _modular_. The framework ships with its own listeners and 
agents while also allowing users to rapidly develop their own highly customized 
listeners and agents.

## What is Consortium?
### Definition
Consortium's above canonical definition — its elevator pitch you might say — is a bit of a 
mouthful. So, lets go over each part, not necessarily in order, to clearly spell out 
what exactly it is.



#### 1. "C2 framework"
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

#### 2. "Programming language agnostic, and networking protocol agnostic"
**Networking protocol agnostic** - As a software framework, Consortium imposes no 
limitations on the types of listeners and agents that can be used. This means that 
listeners and agents can be used in the framework that communicate over any networking 
protocol, regardless of the model or method of communication.

**Programming language agnostic** - Consortium is written entirely in Python so it 
provides a Python based software framework you can build off of. However, the design of 
the framework allows you to remotely hook in listeners and agents written in any 
arbitrary language to the framework over its server's API.

#### 3. "Designed to be collaborative, highly extensible, and modular"
**Collaborative** - Consortium adopts a server-client model to allow collaboration. 
The server manages all C2 related activities while multiple clients can simply connect 
to the same server to perform C2 related operations together.

**Extensible** - The Consortium server exposes a REST API for most C2 related 
functionality. A websockets API is additionally provided to allow for server-pushed 
events to be received. Having a common API means that it is possible to write software 
to extend the framework's capabilities. You can automate actions, write custom hooks, 
and even develop your own custom client based off the API alone.

**Modular** - The Consortium 


### Architecture
There are 4 core components to Consortium. The "client", "server", "listener" and 
"agent". These 4 components form the basis of how communication occurs throughout the 
framework.

## Why Use Consortium?
The concept of a C2 framework that provides reusable software tools to create custom 
listener-agent implementations is not new. In fact, by nature of the design of many 
frameworks it is _in theory_ possible (and sometimes even advertised by said frameworks)
to write your own custom implementations of whatever listener or agent is present in the 
framework.

However, more often than not, the idea of providing tools to create custom 
implementations of listeners or agents for a particular C2 framework is something that 
is more "tacked-on" within the project than something that is a fully realized feature. 
C2 frameworks focus more on the "C2" aspect rather than the "framework" aspect.

Consortium is different in that it aims to take a "framework-first" approach. It is 
built with this idea at the forefront of providing users with the means to create their 
own custom listener-agent implementations.
