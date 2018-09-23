# The PyIris Project
The PyIris project is an attempt at creating a modular, stealthy and flexible remote-access-toolkit. It allows users to 
dynamically build remote-access payloads (referred to as scouts) by loading and unloading specific modules (referred to as components), 
that grant scouts specific features. This allows you to cut down on file size and only use essential features making it
less likely for antivirus to detect the scout. It also allows for highly customisable payloads that have low hard drive footprints as 
the scout never writes anything to the disk.

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

# Features (Linux)
- Coming soon

# Getting Started
## Prerequisites
- Python 2.7
- Git

## Setting up PyIris (Windows)

```git clone https://github.com/angus-y/PyIris-backdoor```
```pip install https://github.com/AndreMiras/pycaw/archive/master.zip```
```pip install -r windows_requirements.txt```

## Setting up PyIris (Linux)

```git clone https://github.com/angus-y/PyIris-backdoor```

## Updating PyIris
Change into the PyIris-backdoor folder first, then run

```git pull```

## Recommended OS
### PyIris was succesfully installed on the following operating systems
- Windows 10
- Kali Linux
- Ubuntu

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

# Built with
[PyCharm IDE](https://www.jetbrains.com/pycharm/)

# Want to report a bug?
Create an issue, but before that please read the "ISSUE_TEMPLATE.md" file first

# Credits
- Inspired by [Powershell Empire](https://github.com/EmpireProject/Empire) and [Brain Damage](https://github.com/mehulj94/BrainDamage)
- Thanks to ev-ev for helping me in the earliest stages of the project and in helping me to create PyIris

# License
Licensed under Mozilla Public License Version 2.0 - See the "LICENESE.md" file for more details

# Disclaimer
I am not held reponsible for anything illegal that you do with this framework, this framework was developed for ethical hackers, 
pentesters and for research purposes. Please do not use this without the full consent of the victim. Use this framework to break stuff 
but legally please :)
