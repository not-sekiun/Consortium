import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from ctypes import windll')
        config.functions.append('''
def admin():
    s.sendall(('[*]Scout is running with admin privileges : ' + str(windll.shell32.IsUserAnAdmin() != 0)).encode())''')
        config.logics.append('''
            elif command == "admin":
                admin()''')
        config.help_menu['admin'] = 'Checks to see if the scout is running as a process with admin privileges'
    elif option == 'info':
        print('\nName             : Check Admin component' \
              '\nOS               : Windows' \
              '\nRequired Modules : ctypes' \
              '\nCommands         : admin' \
              '\nDescription      : Checks to see if the scout is running as a process with admin privileges\n')
