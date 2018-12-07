# Update 0.7.4
- Small but crucial update to the compiler so it now supports pyinstaller compilations that DONT have the --onefile option leading to 
non-packed binaries
- Added a new custom prompt for components that require manual intervention from users
- Reworded some stuff for accuracy


# Yearly update (0.7.2)
Its been about a year since PyIris has come out (WOW happy 1 year anniversary) so heres a quick consolidation of what I've done and 
plan to do.

## First up the changelog
- murdered a few bugs 
- replaced the names of the startup functions
- fixed a path writing error in the persistence module
- updated requirements file to use a new version of cv2 that solves a bug within the webcam module where webcam light would not turn off

## Next up, the roadmap
- Planning on adding encryption between communications? Details are very hazy. There may be more than 1 base component users can choose 
to use should it happen!
- Planning to add 1337 45cii b4n3r5 cause even metasploit has them. Just for fun and some eye candy its no hard so they'll come out 
pretty quickly 
- Of course I will continue to build on my database of components planning on adding some to help in pivoting through networks and 
lateral movement
- Writing a wiki is also on the agenda, unfortunately PyIris' "help" may not be enough.
- Code obfuscation and encryption, to circumbent AV I need to create custom encoders for scouts that could be layered on top of each 
other, eg XOR on top of base64 on top of AES encryption. This will be part of the genretor interface
- Thinking of adding powershell/bash script support so scouts can execute uploaded bash/powershell scripts
- Oh yeah also PyIris is still in Alpha I'm thinking of moving it to BETA bug testing and eventual OFFICIAL RELEASE (v1.0.0) after
completing all the roadmap objectives here, that will take time though, Im still a student and have middle school stuff to deal with...

## Conclusion
I dont expect development of PyIris to be moved to beta until late June maybe??? I still have tons of cool ideas for this project that 
may be put in during development. Dont expect a definite release date or anything. I doubt anyone will read this far but if so MERRY 
CHRISTMAS and thank you for supporting the development of PyIris, seriously just cloning it or star-ing it gives me life.


# Update 0.7.1 (wow this came pretty quickly)
- Added colored output, now all text will have color with the exception of scout sent data
- Prompts also have color
- Added global error handling to catch fatal program errors
- Added defaulting of Windows scouts for windows system and defaulting of Linux scouts for linux systems
- By default Host option of scout generation is no longer 127.0.0.1 it is now your detected primary private IP


# WHOO Update 0.7.0 not like anyone will ever see this...
- Added keystroke injection, you can now force your victim to type things by generating keyboard events in linux and windows
- Changed up the generation of scouts by a bit
- Added windows only interface locking, you can now selectively disable or enable your targets keyboard or mouse
- Removed some left behind debug statements


# Update 0.6.9
- Ported most of the windows components to linux some werent ported due to the fact that linux bash shell is much more versatile than windows cmd, eg. you can get user idle time from the terminal alone
- Fixed a small issue with pinging scouts and detecting dead scouts

# Update 0.6.8
- Added remote python interpreter code execution component
- You can now reference a component by id, instead of loading through "load windows/component" you can load it as "load 1"
- Refactored some code in the show load and unload part for generator
- Removed case sensitivity for commands

# Update 0.6.7
- Added the ability to take pictures from webcam
- Added the option to auto compile windows scouts into portable executables that are either windowed or packed

# Update 0.6.6
- Added the ability to dump saved chrome passwords
- Fixed minor bug with keylogger
- Improved scout generation by reducing duplicate or similar import statements

# Update 0.6.5 (I'm not dead)
- Added TONS of new scout features
- Debugged the generator interface where the generate command was writing duplicate functions
- Added a requirements file, now modules are beginning to require third party libraries
- Also starting to plan to add support for linux based scouts


# Update 0.6.4
- Rewrote persistence module
- Added remote code execution, file execution, file upload, file download and file download from web capabailities to scout as 
components
- Refactored more code
- Addded error handling for socket timeout in direct handler
- Generalized error handling in scouts to reduce file space

# Update 0.6.3
- Changed up the payload generator
- Fixed a few bugs in the generate function and load function
- Added a registry persistence module
- Curently added a "test" remote command execution module, will be adding new modules soon and completing the remote command execution 
module

# Update 0.6.2
- Refactored code
- Rewrote the PyIris framework, changed commands and interface
- Changed payload generation
- Added support for completely customizable payloads
- Changed up the interfaces
- Will now slowly start migrating all other scout features into components you can load onto scouts during payload generation

# Christmas update 0.5.2 :)
- Refactored and debugged handler code
- Added new payloads
- Added the ability to locally enter python interpreter
- Added payload generator handler
- Changed the how listeners are created
- Added fake replies
- Turned payloads into payload templates
- Slightly changed the banners
- Added persistent credentials
- More global default variables can be set
- Added the ability to reset the framework
- Added splash screen at startup
- Renamed a bunch of files
- Changed how files are imported
- Made some reused code into a seperate module altogether
- Changed the scout authentication protocol
- Added the Scout key

# Update 0.4.1
- fixed an issue with sleeping the scouts

# Update 0.4.0
- added local system command execution
- new banner
- added the config checker
- added persistent data
- changed upload and download, now you can upload and download things with duplicate end marker
- renamed files
- banner detects when file was last updated
- changed data layout when displaying scout data
- added alert to show when scout reports back
- ported recon payload to linux
- refactored code yet again

# Update 0.3.0
- added the new windows recon payload(new capabilities and features)
- refactored code(grouped together repeating blocks of code)
- fixed injection payload error where running ty,pr,sh without args would crash the payload
- Added generic exception handler, payload only attempts reconnect on socket.timeout or socket.error

# Update 0.2.0
- added linux payloads
- added input injection (keyboard, mouse and clipboard)
- removed ntpath, termcolor module completely (less dependant on third party modules)
- removed pickles in upload and download
- added failsafe to make payload more robust (in case of server unexpected exit)
