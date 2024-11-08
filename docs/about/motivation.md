# Motivation

There are many well-designed C2 frameworks.

Metasploits's Meterpreter, Powershell-Empire, Cobalt-strike, Covenant, and many others
excel at providing an application for controlling remote systems.

## C2 Frameworks: More "C2" than "Framework"

The concept of a C2 framework that provides reusable software tools to create custom
listener-agent implementations is not new. In fact, by nature of the design of many
frameworks it is _in theory_ possible (and sometimes even advertised by said frameworks)
to write your own custom implementations of whatever listener or agent is present in the
framework.

However, more often than not, the idea of providing software tools to create custom
implementations of listeners or agents for a particular C2 framework is something that
is more "tacked-on" within the project than something that is a fully realized feature.
That is to say that many C2 frameworks focus more on "being a C2" rather than "being a
framework" leading to a poor extensibility experience.
