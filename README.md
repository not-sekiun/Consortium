# The PyIris Project (Ported to python 3 now in PERPETUAL BETA)
The PyIris project is a modular, stealthy and flexible remote-access-toolkit written **completely in python**.
It allows users to dynamically build, generate and encode/encrypt remote-access-trojan payloads for remote
control of other compromised hosts.

# Why should you use this project?
You should'nt lol, this was a passion project made purely for fun. It was never intended or designed to be used professionally in any 
pen-testing or red teaming scenarios. Feel free to poke around with it to see what it can do.

# Demo of PyIris in action on multiple operating systems (Windows and Linux)
## Dynamically generating a payload in Windows
![Windows Generator Demo](https://user-images.githubusercontent.com/32593795/70084865-1db4ca80-164a-11ea-8837-461fdc39a770.png)

## Remotely controlling a Windows system through a scout in Ubuntu (screenshot of victims machine is of the ubuntu attacker machine since I'm running the ubuntu machine in a VM)
![Ubuntu Scout Demo](https://user-images.githubusercontent.com/32593795/70084859-1ab9da00-164a-11ea-867f-2fb6e36106e5.png)

## Creating listeners that will receive connections from the scouts in Kali Linux 
![Kali listener Demo](https://user-images.githubusercontent.com/32593795/70084874-1f7e8e00-164a-11ea-96fb-50fcfd396f11.png)

# Features (Both Windows and Linux)
- Tab completion for most commands
- Dynamically generate scouts
- Robust error handling to allow scouts to recover from sudden disconnects
- Upload and download files from and to the target machine
- Sleep, kill and disconnect scouts
- Download files from external urls (web dowloads)
- Keylogging in memory
- Displaying system information
- Taking screenshots without writing to disk
- See all currently open visible and non visible windows on the target
- Check to see if scout is running with admin/root privileges
- Inject keystrokes
- Compile payloads into Windows EXEs or Linux ELFs
- Clear, set or dump clipboard data
- Setting audio
- Take pictures from webcam without writing to disk
- Stackable encryption of scout payload source code, in a theoretically infinite stack in infinite variations
- execute arbitrary python code and read the results even if the python interpreter is not installed on the target machine from compiled 
scouts
- request for admin/root
- sleep for an arbitrary length of time before running (To bypass AV dynamic program analysis)
- self delete (only works for scripts)
- Stream webcam over TCP sockets

# Features (Windows)
- Acheive persistence through the windows registry (HKEY_CURRENT_USER)
- Acheive persistence through the windows startup folder
- Remote Command Execution through cmd.exe or powershell.exe (provided it is not blocked)
- Open URLs from native browser (internet explorer ewww)
- Shutdown, restart, lock, logoff user gracefully without connection hanging from scout payload
- Execute or open files remotely
- Check the user idle time
- Dump saved chrome passwords
- Disbale/ Enable the targets keyboard/mouse
- Bypass UAC through sdclt.exe (Has already been patched in recent windows updates)

# Features (Linux)
- Achieve persistence through cron jobs (crontab)
- Remote Command Execution through the bash shell

# Getting Started
## Prerequisites
- Python 3.x, (I use python 3.7.x)
- Git

## Setting up PyIris (Windows)

First, clone this repository and cd into the directory, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor```

Next, install the rest of the required modules with pip. Only install modules from the ```setup/windows/requirements.txt``` file
as this section is for running the Windows edition of PyIris.

```pip3 install -r setup/windows/requirements.txt```

Upon running it the first time you should be greeted with the option to generate a key, this indicates everything has been installed
correctly.

## Setting up PyIris (Linux)

First, clone this repository, make sure you have git installed.

```git clone https://github.com/angus-y/PyIris-backdoor```

```cd PyIris-backdoor```

Next install an external dependency, xlib, required by pyperclip through apt-get.

```sudo apt-get install xclip```

Then install pyalsaaudio through apt-get, if you're installing on **ubuntu** please read the below note

```sudo apt-get install python3-alsaaudio```

**NOTE** : For some reason there exists no python3-alsaaudio package for ubuntu that can be installed through apt/apt-get ALTHOUGH the 
python3-alsaaudio package can be installed just fine on kali linux. This means that on ubuntu PyIris will NOT run due to it being unable 
to import alsaaudio in the 3rd party library import testing phase of its bootstrap. Installing from pypi fails as well. You need to 
build the python3-alsaaudio package from source to get PyIris to work on Ubuntu it seems.

Finally, install the rest of the required modules with pip. Only install modules from the ```setup/linux/requirements.txt``` file as
this section is for running the Linux edition of PyIris.

```pip3 install -r setup/linux/requirements.txt```

Upon running it the first time you should be greeted with the option to generate a key, this indicates everything has been installed
correctly.

## Updating PyIris
Change into the PyIris-backdoor folder first, then run

```git pull```

On windows to install any newly added third party modules or update then run

```pip3 install -r setup/windows/requirements.txt```

On linux to install any newly added third party modules or update then run

```pip3 install -r setup/linux/requirements.txt```

## Supported OS
### PyIris was successfully installed on the following operating systems
- Windows 10
- Kali Linux Rolling releases
- Ubuntu 16.04 and future releases (TECHNICALLY supported, although python3-alsaaudio cannot be installed conventionally, see the note 
above at the linux PyIris install section
- Debian

# Basic Usage
## Windows

```py -3 PyIris.py```

If prompted to generate a key, either press enter or enter a key that you want to use.

## Linux

```python3 PyIris.py```

If prompted to generate a key, either press enter or enter a key that you want to use.

## Starting out
The ```help``` command is your friend! Simply run ```help``` to get a list of all commands you can use on a specific interface. For more 
detail about a specific command, run ```help <name of command>``` to get more in depth help about it. Alternatively you can use the 
```?``` command which is an alias for the help command. I am planning to write a wiki soon detailing all the commands and information
you need to use PyIris

# FAQ

### Why cant the compiled scout I generated in my Linux OS run on a Windows target machine? (Or vice versa)
PyIris utilizes Pyinstaller to compile its payloads. It is therefore not possible to cross-compile binaries. That means if you 
generate and compile a scout in Linux the binary only runs in Linux, it works the same for Windows. If you want to cross-compile 
Windows scouts for Linux I suggest you use wine and run PyIris from there otherwise your options are very limited.

### PyHook isn't installing on my Windows OS!
I have already included a PyHook wheel file in the setup/windows folder however that wheel works only for 64 bit versions of Windows.
You may have to manually install PyHook yourself. Go to [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and search for the 
PyHook wheel file that works for your Windows version and download it. Next, pip install using the name of that wheel file.

```pip3 install <name of pyhook wheel file>```

If you downloaded the correct pyhook wheel file it should install succesfully.

### I correctly created my listeners and scouts why are the scouts not connecting to my listeners?
Since the listeners actually open ports on your machine you may have to allow the python 3 interpreter (python.exe) through your 
firewall so that it can actually receive connections. Another reason the scouts are not connecting is that your key could have changed 
the pre generated key prompted during a new PyIris install and run is used to authenticate and connect to the listeners. The scout could 
have been generated with a different key than the one that the listener is expecting, the ```regen``` command at the main home interface 
would have changed the key, alternatively you may have directly edited the resources/PyIris.cred file that contains the key

### Why are there more linux components (backdoor functions) than windows components...
Well this is due to several reasons. First, is the problem of open source code and mulitple distros. Linux has many distrubutions each 
linux distro may be different or have a different system structure than each other linux system. Creating components to cover all of 
them is incredibly difficult. Secondly, is support, simply put some linux systems just dont support some functions out of the box for 
python. Lastly is the fact that the terminal in linux is much more powerful than cmd in windows, therefore a lot more things can be 
accomplished from the terminal than from cmd so there is no need to add extra components, your trusty linux/execute_command_bash will do 
the job for you. For example rather than adding a linux/browser component you can use the xdg-open command to open URLs its supported 
out of the box

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
- Thanks to EV-EV for helping me in the earliest stages of the project and in helping me to create PyIris from its infancy
- Thanks to Dharshan2004 for helping build a part of the in-memory webcam module and testing PyIris on Debian
- Thanks to Ani152 for being my unwilling test subject in testing the PyIris framework
- Thanks to my brain for formulating this whole project

# License
Licensed under Mozilla Public License Version 2.0 - See the "LICENESE.md" file for more details

# Disclaimer!
I am not held reponsible for anything illegal or unethical that you do with this framework, this framework was developed for ethical 
hackers, pentesters and for research purposes as a cyber security project. Please do NOT use this without the full consent of the 
victim. Use this framework to break stuff but legally please :).
