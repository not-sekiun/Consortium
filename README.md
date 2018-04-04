# The PyIris project
The PyIris project is an attempt at creating a modular, stealthy and flexible remote-access-toolkit. This toolkit allows users to 
dynamically build remote-access payloads (referred to as scouts) by loading and unloading specific modules (referred to as components), 
that grant scouts specific features and functions. Want a keylogger that also supports remote command execution? No problem, just load 
on a keylogger module and a remote command execution module onto the scout and hit "generate". This will generate a scout for you that 
does just that. This allows a user to cut down on file size and get rid of useless features making it less likely for antivirus to 
detect the scout.

# Features
- None as of now, planning to migrate them soon

# Getting Started
## Prerequisites
- Python 2.7
- Git

## Setting up PyIris

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor```

## Updating PyIris
Change into the PyIris-backdoor folder first

```git pull```

## Recommended OS
### PyIris was succesfully installed on the following operating systems
- Windows 10
- Kali Linux 2017.2
- Ubuntu 16.04

# Basic Usage
## Windows
```py -2 PyIris.py```

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
Inspired by [Powershell Empire](https://github.com/EmpireProject/Empire) and [Brain Damage](https://github.com/mehulj94/BrainDamage)

# License
Licensed under Mozilla Public License Version 2.0 - See the "LICENESE.md" file for more details

# Disclaimer
I am not held reponsible for anything illegal that you do with this framework, this framework was developed for ethical hackers, pentesters and for research purposes. Please do not use it without the full consent of the victim
