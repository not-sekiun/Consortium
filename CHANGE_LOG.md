# Update 1.1.2 (Webcam streaming update)
- Had a lot of stuff going on with my life regarding school so I couldn't work on this project but I finally added webcam streaming over sockets. As of now the streaming is 
implemented using TCP sockets rather than UDP but its relatively stable. I will probably add in a UDP version sooner or later. Havent tested it on linux but 
it should probably work on linux since im using the cv2 library.
- Also the webcam streaming is not multithreaded it probably should be but if anything this module is a bit of a POC. Ill have to come up with a model to handle the multithreaded
webcam streaming
- Oh yeah it is highly advised not to CTRL-C while streaming the webcam. It may kill everything while frames are being received which will destroy the network protocol 
continuity established between the scout and the server
- Fixed an issue with recv_all to compensate for less data being received than anticipated
- Webcam streaming now supports multiple webcams even usb connected ones

# Update 1.0.2 (Major performance update)
- rewrote communication protocol between scouts and server to use message length bytes which drastically reduces the waiting time between sending messages and receiving responses
- old protocol waited for timeout, new protocol reads header length bytes to determine length of sent message which drastically reduces the waiting time for messages to be sent
- commands are now instantaneous and no longer have that disgusting 4 second window between you sending and receiving data. File transfers are also now noticeably much quicker

# Update 1.0.1
- small bug fix patched another unicode issue with the windows request_admin component. Thanks to Ani152 for finding this bug.

# Update 1.0.0 (Out of Alpha into (probably) Perpetual Beta!!!!) [Written on Nov 12 2019]
Well hello, its been a while and we've jumped from v0.8.1 to v1.0.0 all of sudden. You may be wondering, why are we in 1.0.0? What were the major changes that have been made to the framework?
Well the reason we are now in 1.0.0 is because of the fact that the PyIris framework has undergone a relatively major update. It has undergone quite a bit of an overhaul mostly
during the process of porting it over from Python 2.x to python 3.x. During this porting process I was able to iron out many bugs and make quite a few changes to
the interface and underlying code. For example, the underlying wire protocol of the PyIris framework, particularly the file transfer protocol, has been updated
to now utilize base64 rather than pickles to transfer data. Due to these "major" changes, PyIris 1.0.0 is no longer compatible with 0.8.1 PyIris (now a legacy version) and its scouts. Hence, the increment of
the major semantic versioning number to signify a non backward compatible version of the new framework.

At this point Im pretty sure that I have more or less cemented into place all the core features that I want PyIris to have (the so called essential features).
All thats left to do is to add the other less important "peripheral features". The 1.0.0 version is close enough to my original vision of what this framework would be like 2 years ago when
development started (well actually I wanted a fancy GUI and everything but Im scrapping the GUI idea, python is terrible with GUIs). Due to the fact that I have added mostly
what I wanted to add and the fact that the project is coming very close to my original vision I have decided to bring the project into beta out of the alpha feature adding phase. BUT this does
not mean that PyIris will undergone a feature freeze, Im putting it in perpetual beta, adding in new minor features as time passes (eg new components, encoders, etc.). Therefore, you
can expect more minor updates in the future along with bug fixes. ALSO the PyIris framework just hit its 2nd anniversary (2017 11 NOV was the original creation date) so thats cool
and all. Anyways enough from me, heres the changelog.

- fixed the active commands byte to string issue...
- patched set_audio added new windows command set_audio_range, linux audio ranges default from 0-100 due to alsaaudio this information has been appended to the set_audio linux help page
- patched download_web, urllib2 in python 2 has been replaced with urllib
- patched execute python, StringIO in python 2 is now io in python 3
- patched reg_persist, startup reg_persist and sdclt_uac_bypass. We are now using winreg in python3 rather than _winreg in python 2
- fixed bytestring errors with chromedump, patched chromedump
- fixed byte conversion problems with pickles and strings, added new module for download file transfers "recv_all_download_file", patched download_file
- fixed an error with keyboard interrupting for windows/startup/sleep
- fixed an issue with exec_file in windows
- fixed a python3 type error about dictionary sizes changing during iteration and removal of key value pairs within the dictionary
- fixed a bug with the generator parser and added the ability to do "more_com all" and "more_enc all"
- fixed the reset command that was resetting old values that i forgot to update
- fixed FileNotFoundError being confused with socket.error in the download component through taking into account of exception hierarchies in error handling for scouts (this has slighlty increased the base modules filesize)
- compacted recv_all_download_file with recv_all
- fixed upload_file, rewrote the upload_file wire protocol to utilize base64 to send binary data as ascii since the pyiris wire protocol is text based purely. pickles no longer needed
- fixed download file, rewrote the download file wire protocol to utilize base64 as well, pickles no longer needed.
- fixed the download invalid file error being confused with socket error due to exception hierarchies
- fixed an index error with exec_py_file in direct interface when running the command without a file parameter so direct interface will now catch the error
- fixed screenshotting in linux and windows
- fixed a code sequence bug that affected the robust connection handling of scouts
- removed the python 2 to 3 "six" module from the porting process
- Migrated clip_logger of windows to use pyperclip, same as the linux version to standardize. This change was also made due to the fact that win32clipboard was slightly buggy and would sometimes mess up the clipboard when using clip_clear
- in the bootstrap.py file I added an area that checks to see if the required third party libraries (in their respective OSes) are installed and can be imported
- added history log that show history of scout connections on a specific listener
- added basic tab completion to all interfaces except the direct interface whose commands are influenced by the generated scout itself
- finished refactoring all files in all folders and tested most commands
- fixed an encoding error in the encoders byte to string and vice versa conversion was added
- fixed an issue with the bootstrap module to now reject python 2 interpreters if running using them

**Note:** currently there is a color formatting error in windows cmd when generating a new key during bootstrap this is caused by the way colorama works, essentially colorama color input doesnt work for input() in python due to some encoding issues with the interpreter
so until colorama is patched this issue will persist. A small hack to fix this is to run os.system() which changes the encoding of the terminal so color works again but meh its not a big deal.

**Another Note:** Also tested PyIris in cmder under a windows box and I got a weird bug regarding text colors this is due to the encoding of the cmder terminal itself so again a patch to cmder needs
to be made. The framework is still usable however.

# Update 0.8.1
- Added the XOR Encoder and added a sleep module for windows and linux variant scouts
- Reimplemented server response spoofing for listeners for unauthenticated clients

# Update 0.8.0
- ok that came faster than expected, finally added a functioning aes encoder using fernet from cryptography module

# Update 0.7.9.5
- Finally fixed my extremely buggy generator ID parser system
- minor interface changes with regard to new ID parser system
Inactivity update: Due to sch and other commitments pyiris has received very little updates, have no fear i WILL NOT let this passion 
project die and will continually improve pyiris to be the best it can be. Still scratching my head about the encoders though i may be 
getting close...

# Update 0.7.9
- Added a UAC bypass method that takes advantage of the sdclt.exe process it is not OPSEC safe however since it opens a blank cmd prompt 
that (thankfully) wont cause the elevated process to be killed when it is closed. Problem is I cant kill that blank cmd prompt using the 
scout because the scout is usually not elevated while the prompt is elevated so the scout is unable to kill it the user will have to 
click the gui "x" button to kill it instead ;-;
- Fixed a small bug with the socket_listener module that was not catching an UnboundLocalError exception

# Update 0.7.8.8
- Added ability to change the file icon of the scout that is to be compiled
- Added a new resource folder where PyIris.cred and the default ico file will be stored

# Update 0.7.8.7
- Fixed a problem with the bind to scout system. Binding to a scout that sends no data would lead to the binding client (PyIris) to 
assume that the connection was not successful when it actually was but just didnt receive any data
- Fixed an issue with still shaky but less shaky ID system for generator/encoder component loading and unloading
- Fixed some formatting issues within the terminal TUI
- The AES encoder that was added to the encoder components doesnt actually work lol, I was kinda lazy to take it out, its a work in 
progress need to figure out how to use the AES Steram Cipher rather than the AES block cipher to avoid coming up with a padding 
system.... (oh yeah I may (gotta figure out how) also add an XOR encoding option soon :3)

# Update 0.7.8.6
- Fixed a small OPSEC issue with chromepass dump where a random black window would pop up due to improper piping when task killing 
chrome.exe to gain access to the chrome password SQL database.

# Update 0.7.8.5
- The new generator ID system was slightly shaky so I changed it up and fixed it a bit with some reworks to the UI
- We're getting close to official release, 80% through alpha :)

# Update 0.7.8
Whoopsies, skipped 0.7.7 and 0.7.7.5 changelog entry
- Added a small minor update to the way generator IDs are selected. Now you can use commas to select multiple IDs and dashes for ranges
eg . load_com 1,2,3-5 loads components of ID 1,2,3,4,5
- minor update to loading interface the ID of the components/encoder are displayed in brackets when showing whether loading was 
successful or not
- refactored the load_com, load_enc, more_com, more_enc modules to be more modular

# Update 0.7.6 
:fireworks::fireworks::fireworks::fireworks::fireworks::fireworks::fireworks::fireworks::fireworks:
- HAPPY NEW YEEEAAARRRR, NEW YEAR NEW PYIRIS YEET
- Added new encoders after so long, so far only one, the base64 encoder
- New concept known as the "Encoder stack" its a stack based encoding format where encoding traverses downwards
- Loop encoding works as well so you can encode one scout with the same encoder multiple times not sure if it helps but cool to have, 
nothing says I'm a FUD payload then a python file base64 encoded 100 times
- Made the scout show command more useful now it displays and filters whether scouts are connects through reverse or bind TCP
- changed the load command to load_com (component) command so I can include a load_enc (encoder) command same for unload commands. The 
show command remains the same (show components, show encoders)

# Update 0.7.5
- Added option to choose multiple bases
- Now supports bind tcp scouts, access it with the new "bind" command

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
- ~~Planning to add 1337 45cii b4n3r5 cause even metasploit has them. Just for fun and some eye candy its not hard so they'll come out
pretty quickly~~ (Lmao "quickly" still not added yet. Ill save these for official release.)
- ~~Of course I will continue to build on my database of components planning on adding some to help in pivoting through networks and
lateral movement~~ (Added most of what I really wanted to add. Even after 1.0.0 I will continue adding so this is off the map now)
- Writing a wiki is also on the agenda, unfortunately PyIris' "help" may not be enough.
- ~~Code obfuscation and encryption, to circumvent AV I need to create custom encoders for scouts that could be layered on top of each
other, eg XOR on top of base64 on top of AES encryption. This will be part of the genretor interface~~ (DONE, now the only work I need to
do is to add even MOAR types of encoders)
- ~~Thinking of adding powershell/bash script support so scouts can execute uploaded bash/powershell scripts, time to live off the land~~ (Sort
of bamboozled on how to do this I know you can execute files on disk with exec_c/exec_b but I want this to be in memory, will need to do more
research i guess its off the map for now)
- ~~Oh yeah also PyIris is still in ALPHA I'm thinking of moving it to BETA bug testing and eventual OFFICIAL RELEASE (v1.0.0) after
completing all the roadmap objectives here, that will take time though, Im still a student and have high school stuff to deal with...~~ (Finally in perpetual beta after 2 years)
- Gotta add support for other compilers like py2exe or nutika wine pyinstaller exes get falsely flagged by AV, also gonna add the 
ability to change the compiled exes file icon
- In order to bamboozle AV even more Im thinking of adding a trash code generator that generates useless code in python and comments
that will still change the file signature even more wont help against heuristic behavioral detection but we can bamboozle static 
detection
- ~~planning to add tab completion so I dont have to type as much (pyreadline, gnureadline)~~ (DONE)

## Conclusion
I dont expect development of PyIris to be moved to beta until late June maybe??? (Hi this is me from the future, development is taking 
even longer due to external commitments and school ;-; beta will come maybe by the end of the year now that I am free) I still have tons 
of cool ideas for this project that may be put in during development. Dont expect a definite release date or anything. I doubt anyone 
will read this far but if so MERRY CHRISTMAS and thank you for supporting the development of PyIris, seriously just cloning it or 
staring it gives me life.


# Update 0.7.1
- Added colored output, now all text will have color with the exception of scout sent data
- Prompts also have color
- Added global error handling to catch fatal program errors
- Added defaulting of Windows scouts for windows system and defaulting of Linux scouts for linux systems
- By default Host option of scout generation is no longer 127.0.0.1 it is now your detected primary private IP


# Update 0.7.0
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

# Update 0.6.5
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
