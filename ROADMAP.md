# The Future of PyIris
A short collection of ideas and concepts I have planned for PyIris in the future upcoming updates. I'm pretty busy with life so theres no 
set date on when these goals will be fulfilled, could be finished in a duration of weeks to years. 

## 2021 update [Added 9/6/2021]
So I havent worked on this project in a while mainly due to school and life stuff so that kind of sucks. Im finishing my exams soon so I will very soon have time to work on the
project. Ive decided to make a bunch of code changes with regards to the internal functioning of PyIris, ie with how the in memory database is managed, how listeners are set
etc. I dont have much time to write this so here are a few new things I want to do with the project moving forward

- Change the in memory database housing listeners from a dictionary based model to an object oriented model
- Add more types of listeners and scout bases (Droppers!) to expand the communications channel (encryption is coming soon I promise + algorithmic key cycling maybe)
- tweak a bit of how some of the components work (the exec_c, exec_p, exec_b commands for remote shell execution are VERY annoying to use especially when you want to quickly 
execute things or shift through the filesystem I will probably do what meterpreter does to save me the hassle
- Update some components, some components like chrome password grabbing no longer work on updated systems 
- Expand component functionality. I want more options when it comes to doing stuff in general (ie file upload and download doesnt work with file directories they are limited to 
single files only. Or webcam streaming is trash since it works over TCP)
- Expand AV evasion capabilities. Windows defender flags PyIris payloads as malicious (for some reason the sysinfo component triggers the AV. I may need to look into better AV 
evasion measures
- Change how listeners are loaded (to be more similar to meterpreter for greater variability in listener types) and how scouts are generated (again more similar to meterpreter to 
allow for more variability)


## Short Term Goals
- Port all the webcam based operations, over from using cv2 to just using PIL, because its stupid getting people to import a computer 
vision library for the sole purpose of watching people through their webcams [Added 4/26/2020]
- Implement a webcam streaming feature (!!!). [Added 4/26/2020] :white_check_mark: [done 7/18/2020]
- Fix some instability issues with the recv_all() network protocol. (rate limiting is not working) [Added 4/26/2020] :white_check_mark: [done 7/18/2020]
- Possibly implement a screen recording function as well. [Added 4/26/2020]
- Look into audio streaming/ recording if possible. [Added 4/26/2020]
- Possibly get scouts to provide more data upon connecting back [Added 4/26/2020]


## Long Term Goals
- Add communications encryption (Maybe AES, maybe RSA) encryption between scouts using the standard text data protocol [Added 4/26/2020]
- Add support for more scout bases (An HTTP base maybe could be possible, Discord base, Telegram base, Twitter Base, Reddit. I even have 
an absurd idea for scout communication using roblox will look into and do more research about this) [Added 4/26/2020]
- Continue to add more advanced features, I have a few more features I want to implement for the scouts relating to machine persistence, 
command and control functionality, credential exfiltration and even some social engineering elements. The ideas are vague so I need to 
sketch them out fully before moving them to short term. [Added 4/26/2020]
~~- Currently working on implementing a GUI/ web interface in collaboration with a close friend of mine (more like hes doing all the front 
end lol). Details are still hazy although the prototype is mostly finished I may need to ensure backend stability/ optimization before 
rolling out the release [Added 4/26/2020]~~ This is kinda screwed since im changing a whole bunch of stuff at once. I may or may not decide to add a GUI at this point I dont know.
- Figure out how to dynamically load python modules. Not sure if this is possible at all. If so, it may completely change the entire 
course of this project. Will do more research and look into it. [Added 4/26/2020]
