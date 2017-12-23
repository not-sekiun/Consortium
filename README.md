<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/33884151-8f69ad80-df79-11e7-846e-3b766d4a9f0d.png" width="200" />
</p>
# PyIris
PyIris (the shortened name of Python-Iris), is a post exploitation, reverse shell, backdoor toolkit used in order to gain access onto 
remote systems stealthily. PyIris utilises cross-platform, reverse TCP payloads that can effectively evade modern antivirus, firewalls 
and user detection even after being compiled into executable files.

# Screenshots
## Main Handler
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34318519-fe0c560a-e804-11e7-8320-868bc551912c.png" />
</p>

## Listener Handler
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34318521-fe868e2a-e804-11e7-9386-2ed5db0202c0.png" />
</p>

## Scout/Generic Handler
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34318518-fdd20bee-e804-11e7-8379-11d869614577.png" />
</p>

## Generator Handler
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34318520-fe552538-e804-11e7-96dd-c7416b3c25de.png" />
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
- Take a webcam snapshot
- Generate payloads

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
- Python 3.X (Only for linux)
- Python pip
- Git/Git bash

## Setup(Ubuntu)

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor\setup```

```sudo python linux_set_pip.py```

```sudo pip install -r linux_requirements.txt```

```python set_creds.py```

## Setup(Kali Linux)

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor\setup```

```python linux_set_pip.py```

```pip install -r linux_requirements.txt```

```python set_creds.py```

## Setup(Windows)

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor\setup```

```pip install -r windows_requirements.txt```

```py -2 set_creds.py```

The path does not have to be the one mentioned above, use the absolute path to your version of pip2.

## Updating PyIris
PyIris is a project undergoing heavy development and debugging, make sure to update often by running these commands in the PyIris
folder. Check out CHANGELOG.md in the repo to see whats new, whats removed and whats fixed.

```git pull```

```pip install -r linux_requirements.txt/windows_requirements.txt```

The pip install depends on your operating system(Linux/Windows).

## Recommended OS
PyIris was installed succesfully on the following Operating Systems and therfore it is recommended to use these Operating Systems.

- Windows 10
- Ubuntu 16.04
- Kali Linux 2017.2

If you are runnning a different operating system and have trouble installing please contact me and let me know. (See title below Bugs, Suggestions or inquiries)

# Basic Usage
Change into the PyIris-backdoor directory

## Running the server in Windows cmd/powershell
```py -2 PyIris.py```

## Running the server in Linux terminal
```sudo python PyIris.py```

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
