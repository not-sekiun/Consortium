# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from ctypes import Structure, windll, c_uint, sizeof, byref')
        config.functions.append('''
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def idle(data):
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    s.sendall('[+]User has been inactive for : ' + str(millis / 1000.0))''')
        config.logics.append('''
            elif command == "idle":
                idle(data)''')
        config.help_menu['idle'] = 'Get amount of time user has not pressed a key or moved mouse/ get the idle time of system'
    elif option == 'info':
        print '\nName             : Get Idle component' \
              '\nOS               : Windows' \
              '\nRequired Modules : ctypes' \
              '\nCommands         : idle' \
              '\nDescription      : Get amount of time user has not pressed a key or moved mouse/ get the idle time of system\n'
