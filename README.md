# The PyIris Project
The PyIris project is a modular, stealthy and flexible remote-access-toolkit. It allows users to dynamically build, generate and encode 
remote-access-trojan payloads for remote control of other compromised hosts.

# Demo of PyIris in action on multiple operating systems (Windows and Linux)
## Dynamically generating a payload in Windows
![Windows Generator Demo](https://user-images.githubusercontent.com/32593795/47714521-0f8ec080-dc78-11e8-8004-490eaff4f4f2.png)

## Remotely controlling a Windows system through a scout in Ubuntu
![Ubuntu Scout Demo](https://user-images.githubusercontent.com/32593795/47714519-0dc4fd00-dc78-11e8-93b2-8e6811036910.png)

## Creating listeners that will receive connections from the scouts in Kali Linux 
![Kali listener Demo](https://user-images.githubusercontent.com/32593795/47714529-11f11a80-dc78-11e8-81e7-6f18b3608948.png)


# Features (Windows)
- Dynamic generation of scouts
- Windows registry persistence
- Sleep, kill and disconnect scouts
- Robust error handling
- Remote Command Execution through CMD
- Remote Command Execution through Powershell
- File transfer and data exfiltration
- Shutdown, restart, lock, logoff user
- Download files through url
- Execute and open files remotely
- Keylogging in memory
- Taking screenshots in memory
- Setting audio
- Displaying system information
- Getting user idle time
- Clear, set, dump clipboard data
- Check to see if scout is running with admin privileges
- See all currently open windows on the target
- Dump saved chrome passwords
- Take pictures from webcam without writing to disk
- Compile payloads into Windows EXE
- Inject keystrokes
- Disbale/ Enable the targets keyboard/mouse
- Bypass UAC through sdclt.exe
- Stackable encryption of scout payload source code, in a theoretically infinite stack in infinite variations 

# Features (Linux)
- Dynamic generation of scouts
- Sleep, kill and disconnect scouts
- Robust error handling
- Remote Command Execution through bash shell
- File transfer and data exfiltration
- Download files through url
- Keylogging in memory
- Taking screenshots in memory
- Setting audio
- Displaying system information
- Clear, set, dump clipboard data
- Check to see if scout is running as root
- See all currently open windows on the target
- Take pictures from webcam without writing to disk
- Compile payloads into Linux ELF
- Inject keystrokes
- Stackable encryption of scout payload source code, in a theoretically infinite stack in infinite variations 

# Getting Started
## Prerequisites
- Python 2.7
- Git

## Setting up PyIris (Windows)

First, clone this repository, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

Next, pip install pycaw, which can't be installed the standard way, so you'll need to install pycaw from this separate github repository

```pip install https://github.com/AndreMiras/pycaw/archive/master.zip```

Finally, install the rest of the required modules the standard way. Only install modules from the "setup/windows/requirements.txt" file 
as this section is for running the Windows edition of PyIris.

```pip install -r setup/windows/requirements.txt```

Upon running it the first time you should be greeted with the option to generate a key, this indicates everything has been installed
correctly.

## Setting up PyIris (Linux)

First, clone this repository, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

Next install an external dependency, xlib, required by pyperclip.

```sudo apt-get install xclip```

Then install pyalsaaudio through apt-get

```sudo apt-get install python-alsaaudio```

Finally, install the rest of the required modules the standard way. Only install modules from the "setup/linux/requirements.txt" file as
this section is for running the Linux edition of PyIris.

```pip install -r setup/linux/requirements.txt```

Upon running it the first time you should be greeted with the option to generate a key, this indicates everything has been installed
correctly.

## Updating PyIris
Change into the PyIris-backdoor folder first, then run

```git pull```

On windows to install any newly added third party modules or update then run

```pip install -r setup/windows/requirements.txt```

On linux to install any newly added third party modules or update then run

```pip install -r setup/linux/requirements.txt```

## Recommended OS
### PyIris was succesfully installed on the following operating systems
- Windows 10
- Kali Linux Rolling releases
- Ubuntu 16.04 and future releases
- Debian

# Basic Usage
## Windows

```PyIris.py```

If prompted to generate a key, either press enter or enter a key that you want to use.

## Linux

```python2 PyIris.py```

If prompted to generate a key, either press enter or enter a key that you want to use.

## Starting out
The ```help``` command is your friend! Simply run ```help``` to get a list of all commands you can use on a specific interface. For more 
detail about a specific command, run ```help <name of command>``` to get more in depth help about it. Alternatively you can use the 
```?``` command which is an alias for the help command. 

# FAQ

### Why cant the compiled scout I generated in Linux run on Windows? (Or vice versa)
PyIris utilizes Pyinstaller to compile its payloads. It is therefore not possible to cross-compile binaries. That means if you 
generate and compile a scout in Linux the binary only runs in Linux, it works the same for Windows. If you want to cross-compile 
Windows scouts for Linux I suggest you use wine and run PyIris from there.

### PyHook isnt installing on my Windows OS!
I have already included a PyHook wheel file in the setup/windows folder however that wheel works only for 64 bit versions of Windows.
You may have to manually install PyHook yourself. Go to [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and search for the 
PyHook wheel file that works for your Windows version and download it. Next, pip install using the name of that wheel file.

```pip install <name of pyhook wheel file>```

If you downloaded the correct pyhook wheel file it should install succesfully.

### Why are there more linux components (backdoor functions) than windows components...
Well this is due to several reasons. First, is the problem of open source code and mulitple distros. Linux has many distrubutions each 
linux distro may be different or have a different system structure than each other linux system. Creating components to cover all of 
them is incredibly difficult. Secondly, is support, simply put some linux systems just dont support some functions out of the box for 
python. Lastly is the fact that the terminal is much more powerful than cmd, therefore a lot more actions can be accomplished from the 
terminal than from cmd so there is no need to add extra components, your trusty linux/execute_command_bash will do the job for you

### Why are you using a raw text protocol isn't something like HTTP less suspicious to network analyst
Yes it is I should probably be using HTTP buuuuut I am just lazy. Perhaps in a future update but that requires rewriting a lot of the 
listener-scout protocol which could take some time.

### Hey I am a 1337 H4X0R and need to DDOS NSA and The Pentagon can you add a 1337 DDOS component
No lol

# Built with
- [PyCharm IDE](https://www.jetbrains.com/pycharm/)
- My brain

# Want to report a bug?
Create an issue, but before that please read the "ISSUE_TEMPLATE.md" file first

# Credits
- Inspired by [Powershell Empire](https://github.com/EmpireProject/Empire) and [Brain Damage](https://github.com/mehulj94/BrainDamage)
- Thanks to ev-ev for helping me in the earliest stages of the project and in helping me to create PyIris
- Thanks to Dharshan2004 for helping build a part of the in-memory webcam module and test PyIris on Debian
- Thanks to my brain for formulating this whole project

# License
Licensed under Mozilla Public License Version 2.0 - See the "LICENESE.md" file for more details

# Disclaimer!
I am not held reponsible for anything illegal or unethical that you do with this framework, this framework was developed for ethical 
hackers, pentesters and for research purposes as a cyber security project. Please do NOT use this without the full consent of the 
victim. Use this framework to break stuff but legally please :).
