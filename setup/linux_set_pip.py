import os
import platform

commands = ['pip install python3-xlib','apt-get install scrot','apt-get install python3-tk','apt-get install python3-dev',
            'apt-get install portaudio19-dev','apt-get install python-alsaaudio','apt-get install python-wnck']

if platform.uname()[0] == 'Linux':
    if os.getuid() == 0:
        print '[*]Automatically running these following commands :\n'
        for i in commands:
            print i
        print '\n'
        for i in commands:
            print '\n\n[+]Running : ' + i + '\n\n'
            os.system(i)
        print '[+]Done'
    else:
        print '[-]Run as root'
else:
    print '[-]Only run this on linux'