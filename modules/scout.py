import time,cfg
from modules.banner import *
from modules.wipe import *
from modules.clean import *
from modules.handler import *

cfg.global_variables()


def scout_console():
    while True:
        try:
            input = raw_input(cfg.prompt_scouts).strip().split(' ')
            command = input[0]
            if command == 'banner':
                display_banner()
            elif command == 'help':
                print cfg.help_scouts
            elif command == 'quit':
                cleanup()
            elif command == 'clear':
                clear()
            elif command == 'back':
                print '\n' + cfg.pos + 'Returning...'
                return
            elif command == 'bridge':
                found_target = False
                try:
                    tar_id = input[1]
                except IndexError:
                    print cfg.err + 'Argument needs to be a scout ID, eg. "bridge 1"'
                    continue
                for i in range(len(cfg.db_scouts)):
                    if str(cfg.db_scouts[i][0]) == tar_id:
                        found_target = True
                        tar_id = i
                        break
                if found_target:
                    Pyiris_handler(tar_id)
                else:
                    print cfg.err + 'ID does not exist'
            elif command == 'kill':
                killed_scout = False
                try:
                    tar_id = input[1]
                except IndexError:
                    print cfg.err + 'Argument needs to be a scout ID, eg. "kill 1"'
                    continue
                for i in cfg.db_scouts:
                    if str(i[0]) == tar_id:
                        i[5].sendall('terminate' + End)
                        print cfg.pos + 'Terminated scout : ' + str(i[0])
                        killed_scout = True
                        cfg.db_scouts.pop(cfg.db_scouts.index(i))
                        break
                if not killed_scout:
                    print cfg.err + 'Could not kill scout of ID : ' + str(tar_id)
            elif command == 'kill_all':
                if cfg.db_scouts:
                    for i in cfg.db_scouts:
                        i[5].sendall('terminate' + End)
                    cfg.db_scouts = []
                    print cfg.pos + 'Terminated all'
                else:
                    print cfg.err + 'No connected scouts'
            elif command == 'show':
                print '\n' + cfg.note + 'Currently active scouts :\n'
                if cfg.db_scouts:
                    print 'ID\tIP\t\tUser info\t\tType of scout\tOperating System\n==\t==\t\t=========\t\t=============\t================'
                    for i in cfg.db_scouts:
                        print str(i[0]) + '\t' + str(i[1]) + '\t' + str(i[2]) + '\t' + str(i[3]) + '\t' + str(i[4])
                    print '\n'
            elif command == '':
                pass
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
            print cfg.err+'Error running command "'+command+'"  : '+str(e)
