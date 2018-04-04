# Update 0.6.2
- Refactored code
- Rewrote the PyIris framework, changed commands and interface
- Changed payload generation
- Added support for completely customizable payloads
- Changed up the interfaces
- Will now slowly start migrating all other scout features to the components you can load onto scouts during payload generation

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
