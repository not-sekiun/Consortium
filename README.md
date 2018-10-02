# The PyIris Project
The PyIris project is a modular, stealthy and flexible remote-access-toolkit. It allows users to dynamically build remote-access 
payloads (referred to as scouts) by loading and unloading specific modules (referred to as components), that grant scouts specific 
features. This allows you to cut down on file size and only use essential features making it less likely for antivirus to detect the 
scout. It also allows for highly customisable payloads that have low hard drive footprints as the scout never writes anything to the 
disk.

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
- Compile payloads into Windows EXE or Linux ELF

# Features (Linux)
- Coming soon

# Getting Started
## Prerequisites
- Python 2.7
- Git

## Setting up PyIris (Windows)

First, clone this repository, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

Next, pip install pycaw, which can't be installed the standard way, so you'll need to install pycaw from this separate github repository

```pip install https://github.com/AndreMiras/pycaw/archive/master.zip```

Then, go to [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and look for the file titled "pyHook-1.5.1-cp27-cp27m-
win_amd64.whl" which is the wheel for pyHook. Change into the directory of that wheel and run the following command to install pyHook. 
(Note: Install the correct wheel for your python installation. My python installation is 64 bit so I used the "win_amd64" version of the 
wheel)

```pip install pyHook-1.5.1-cp27-cp27m-win_amd64.whl```

Finally, install the rest of the required modules the standard way. Only install modules from the "windows_requirements.txt" file as
this section is for running the Windows edition of PyIris.

```pip install -r windows_requirements.txt```

Upon running it the first time you should be greeted with the option to generate a key, this indicates everything has been installed
correctly.

## Setting up PyIris (Linux)

First, clone this repository, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

Upon running it the first time you should be greeted with the option to generate a key, this indicated everything has been installed
correctly.

## Updating PyIris
Change into the PyIris-backdoor folder first, then run

```git pull```

## Recommended OS
### PyIris was succesfully installed on the following operating systems
- Windows 10
- Kali Linux
- Ubuntu
- Debian (Tested by Dharshan2004)

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

<details>
<summary>Why cant the compiled scout I generated in Linux run on Windows? (Or vice versa)</summary>
<br>
PyIris utilizes Pyinstaller to compile its payloads. It is therefore not possible to cross-compile binaries. That means if you 
generate and compile a scout in Linux the binary only runs in Linux, it works the same for Windows. If you want to cross-compile 
Windows scouts for Linux I suggest you use wine and run PyIris from there.
<br><br>
</details>

# Built with
[PyCharm IDE](https://www.jetbrains.com/pycharm/)

# Want to report a bug?
Create an issue, but before that please read the "ISSUE_TEMPLATE.md" file first

# Credits
- Inspired by [Powershell Empire](https://github.com/EmpireProject/Empire) and [Brain Damage](https://github.com/mehulj94/BrainDamage)
- Thanks to ev-ev for helping me in the earliest stages of the project and in helping me to create PyIris
- Thanks to Dharshan2004 for helping build a part of the in-memory webcam module

# License
Licensed under Mozilla Public License Version 2.0 - See the "LICENESE.md" file for more details

# Disclaimer!
I am not held reponsible for anything illegal that you do with this framework, this framework was developed for ethical hackers, 
pentesters and for research purposes. Please do not use this without the full consent of the victim. Use this framework to break stuff 
but legally please :)
