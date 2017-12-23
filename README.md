<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/33884151-8f69ad80-df79-11e7-846e-3b766d4a9f0d.png" width="200" />
</p>

# Python-Iris(PyIris)

PyIris (the shortened name of Python-Iris), is a remote-access-toolkit used in order to gain access onto 
remote systems stealthily. PyIris utilises cross-platform, reverse TCP payloads that can effectively evade modern antivirus, firewalls 
and user detection even after being compiled into executable files.

# Demo Screenshots
## Main Handler
<p float="left">
  <img src="https://user-images.githubusercontent.com/32593795/34318673-a3cd4a14-e809-11e7-97d4-1e0a6154b56d.png" />
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
- Send "Fake replies" to programs that cannot be identified as a scout

# PyIris' Arsenal
## Handler
The handler, as it's name suggest takes care of handling listeners, scouts or payload generation. It is the UI of the framework and 
allows you to easily and quickly manage listeners, scouts and generation of payloads

## Listener
The listener's job is to wait on a specific interface and port(0.0.0.0:9999 by default) and wait for connections. Once
a program connects back, the listener initiates the scout authentication protocol to determine whether the connection was initiated by a 
scout or by another program. If the program can identify itself as a scout, the listener lets it in, otherwise the listener sends a fake 
reply to the program and closes the connection.

## Scouts
These are the payloads that connect back to the listener using a reverse TCP conneciton. They are scripted in python and can be compiled 
into stealthy evasive executable files. Each payload has its own core function, such as acting as a reverse shell, injecting user input, 
initiating cyber reconnaissance or simply just acting as a transport to download and launch files from the attacker. 

## Generator
The generator offer a simple, easy to use interface to allow you to configure and quickly generate a scout payload to connect back to a 
specified IP and port.

# Getting Started
## Prerequisites
- Python 2.7
- Python 3.X (Only for linux)
- Python pip
- Git/Git bash

## Setup(Ubuntu)

```git clone https://github.com/angus-y/PyIris-backdoor```

```chmod -R a-x,o-w,+X PyIris-backdoor```

```cd PyIris-backdoor/setup```

```sudo python linux_set_pip.py```

```sudo pip install -r linux_requirements.txt```

```python set_creds.py```

## Setup(Kali Linux)

```git clone https://github.com/angus-y/PyIris-backdoor```

```chmod -R a-x,o-w,+X PyIris-backdoor```

```cd PyIris-backdoor/setup```

```python linux_set_pip.py```

```pip install -r linux_requirements.txt```

```python set_creds.py```

## Setup(Windows)

Run the first command in gitbash before navigating to the folder where the PyIris-backdoor folder is downloaded and running the rest of 
the commands

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor/setup```

```pip install -r windows_requirements.txt```

```py -2 set_creds.py```

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

If you are runnning a different operating system and have trouble installing please contact me and let me know. (See title below Bugs, 
Suggestions or inquiries)

# Basic Usage
Change into the PyIris-backdoor directory

## Running the server in Windows
```py -2 PyIris.py```

## Running the server in Linux
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
Licensed under Mozilla Public License Version 2.0, see LICENESE.md for more details

# Disclaimer
I do not support the illegal or unethical use of this framework. This was developed for research purposes only and should not be used
without the full consent of the target.
