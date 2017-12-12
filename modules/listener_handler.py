import socket, cfg, time, subprocess
from threading import Thread
from modules.show_banner import *
from modules.clear_screen import *
from modules.socket_listener import *
from modules.cleanup_code import *

cfg.global_variables()


def listener_console():
    while True:
        try:
            input = raw_input(cfg.prompt_listener).strip().split(' ', 1)
            command = input[0]
            if command == 'banner':
                display_banner()
            elif command == 'help':
                print cfg.help_listener
            elif command == 'quit':
                cleanup()
            elif command == 'clear':
                clear()
            elif command == 'back':
                print '\n' + cfg.pos + 'Returning...'
                return
            elif command == 'kill':
                killed_thread = False
                try:
                    tar_id = int(input[1])
                except:
                    print cfg.err + 'Argument needs to be a listener ID, eg. "kill 1"'
                    continue
                for i in cfg.db_listeners:
                    if str(i[0]) == str(tar_id):
                        cfg.db_listeners.pop(cfg.db_listeners.index(i))
                        print cfg.pos + 'Killed active listener with ID : ' + str(tar_id)
                        killed_thread = True
                        break
                if not killed_thread:
                    print cfg.err + 'Listener of ID "' + str(tar_id) + '" does not exist'
            elif command == 'kill_all':
                print cfg.pos + 'Killing all active listeners...'
                cfg.db_listeners = []
            elif command == 'start':
                try:
                    port = int(input[1])
                except:
                    print cfg.err + 'Argument needs to be an integer'
                    continue
                t = Thread(target=start_listening, args=(port,))
                t.start()
                time.sleep(2)
            elif command == 'show':
                print '\n' + cfg.note + 'Currently active listeners :\n'
                if cfg.db_listeners:
                    listener_data = [['ID', 'Port'], ['==', '====']]
                    for i in cfg.db_listeners:
                        listener_data.append([str(i[0]), str(i[1])])
                    col_width = max(len(word) for row in listener_data for word in row) + 2
                    for row in listener_data:
                        print "".join(word.ljust(col_width) for word in row)
                    print '\n'
            elif command == '':
                pass
            elif command == 'local':
                try:
                    execute = input[1]
                    print '\n' + cfg.note + 'Executing on system...\n'
                except IndexError:
                    print cfg.err + 'Specify a local system command to run'
                    continue
                if execute[:3] == 'cd ':
                    try:
                        execute = execute.replace('cd ', '')
                        os.chdir(execute)
                        print cfg.pos + "Changed to directory : " + execute
                    except (WindowsError, OSError):
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
            else:
                print cfg.err + 'Unknown command "' + command + '", run "help" for help menu'
        except EOFError:
            try:
                time.sleep(3)
            except KeyboardInterrupt:
                cleanup()
        except KeyboardInterrupt:
            cleanup()
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)
