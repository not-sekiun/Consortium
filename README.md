# PyIris
PyIris (shortened version of Python-Iris), is a post exploitation reverse shell toolkit used in order to gain access onto remote systems. 
PyIris utilises multi-platform, reverse TCP payloads that can effectively evade antivirus, firewalls and user detection even after being 
compiled into executable files. At it's core PyIris' payloads are reverse shells, however these "reverse shells" contain much more 
functionality than just remote command execution. They can transfer files, download from the web, inject user input and do more than a 
normal backdoor payload.

# PyIris' Arsenal
## Handler
The handler is the command and control server of PyIris, it manages listeners and scouts. It's aim is to provide an easy to use interface 
to allow the user to communicate and command the various payloads deployed onto remote systems.
## Listener
The main aim of the listener is to sit and wait for the payloads to connect back to the command and control server. The listener 
refers to a "server key" that each payload is outfitted with. If the payload sends the correct key to the server it is granted access, 
otherwise the connection is torn down and rejected.
## Scouts
These are the payloads that connect back to the handler. They are scripted in python and can be compiled into stealthy evasive executable 
files. Each payload has its own core function such as remote code execution, input injection, cyber reconnaissance and so on. These scouts 
can be easily deployed, each has an ip and port variable that tell it where to connect back to, these are modified and then deployed, 
either as exectuables or .py files which attempt to connect back to the server.

# PyIris' Features
- Remote command execution
- File transfers
- Remote Keystroke injection
- Remote clipboard manipulation
- Mouse movement and input manipulation
