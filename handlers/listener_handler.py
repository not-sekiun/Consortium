import os
import time
import threading
import modules.cfg as cfg
import modules.show_banner as show_banner
import modules.clear_screen as clear_screen
import modules.socket_listener as socket_listener
import modules.cleanup_and_exit as cleanup_and_exit
import modules.execute_local_command as execute_local_command

cfg.global_variables()

def listener_handler_console():
    listener_default_values = {'Hostname':['0.0.0.0','Host Address to listen on'],
                               'Port':[9999,'Host Port to listen on'],
                               'Key':[cfg.listener_key,'Accepted listener key to allow scout to connect to listener'],
                               'FakeReply':[cfg.fake_reply,'Fake reply to send to any program that is not identified as a scout']}
    while True:
        try:
            command_input = raw_input(cfg.prompt_listener).strip()
            option = command_input.split(' ')[0]
            if option == 'banner':
                show_banner.banner()
            elif option == 'clear':
                clear_screen.clear()
            elif option == 'help':
                print cfg.listener_help_menu
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
            elif option == 'configs':
                config = [['    Option','Value','Information'],['    ======','=====','===========']]
                for o,v in listener_default_values.items():
                    config.append(['    ' + o,str(v[0]),v[1]])
                print '\n'
                l = [len(max(i, key=len)) for i in zip(*config)]
                print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                                for item in config)) + '\n'
            elif option == 'kill':
                try:
                    if command_input.split(' ')[1] == 'all':
                        if cfg.db_listeners:
                            cfg.db_listeners = []
                            print cfg.note + 'Killing all active listeners...'
                            while len(threading.enumerate()) > 1:
                                continue
                            continue
                        else:
                            print cfg.err + 'No active listeners'
                    killed_thread = False
                    for i in cfg.db_listeners:
                        if i[0] == int(command_input.split(' ')[1]):
                            cfg.db_listeners.pop(cfg.db_listeners.index(i))
                            killed_thread = True
                            time.sleep(5)
                            break
                    if not killed_thread:
                        print cfg.err + 'Invalid Listener ID'
                except (IndexError,ValueError):
                    print cfg.err + 'Invalid Listener ID'
            elif option == 'set':
                try:
                    listener_default_values[command_input.split(' ')[1]][0] = command_input.split(' ',2)[2]
                    print cfg.pos + 'Set ' + command_input.split(' ')[1] + ' to ' + command_input.split(' ',2)[2]
                except (IndexError,KeyError):
                    print cfg.err + 'Invalid syntax, specify valid option and value'
            elif option == 'show':
                print '\n' + cfg.note + 'Currently active listeners :\n'
                if cfg.db_listeners:
                    listener_data = [['ID', 'Hostname','Port','Accepted Key'], ['==', '========', '====','============']]
                    for i in cfg.db_listeners:
                        listener_data.append([str(i[0]), str(i[1]),str(i[2]),str(i[3])])
                    l = [len(max(i, key=len)) for i in zip(*listener_data)]
                    print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                                    for item in listener_data)) + '\n'
            elif option == 'start':
                try:
                    host = listener_default_values['Hostname'][0]
                    port = int(listener_default_values['Port'][0])
                    listener_access_key = listener_default_values['Key'][0]
                    fake_reply_for_listener = listener_default_values['FakeReply'][0]
                    t = threading.Thread(target=socket_listener.start_listener, args=(host,port,listener_access_key,fake_reply_for_listener))
                    t.start()
                    time.sleep(3)
                except (IndexError,ValueError, TypeError):
                    print cfg.err + 'Invalid IP address/Port number'
                    continue
            elif option == 'reset':
                listener_default_values = {'Hostname': ['0.0.0.0', 'The listeners address to listen on'],
                                           'Port': [9999, 'The listeners port to listen on'],
                                           'Key': [cfg.listener_key,'The key that needs to be sent in order to connect to the listener'],
                                           'FakeReply': [cfg.fake_reply,'Fake reply to send to any program that is not identified as a scout']}
                print cfg.pos + 'Reset current configurations'
            elif option == '':
                pass
            else:
                print cfg.err + 'Unknown command "' + command_input + '", run "help" for help menu'
        except EOFError:
            time.sleep(2)
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)