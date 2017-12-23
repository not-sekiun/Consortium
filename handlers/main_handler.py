import os
import time
import modules.set_globals as set_globals
import modules.cfg as cfg
import modules.change_session_values as change_session_values
import modules.show_banner as show_banner
import modules.cleanup_and_exit as cleanup_and_exit
import modules.clear_screen as clear_screen
import handlers.listener_handler as listener_handler
import handlers.scout_handler as scout_handler
import modules.splash_screen as splash_screen
import modules.execute_local_command as execute_local_command
import handlers.generator_handler as generator_handler

cfg.global_variables()


def main_handler_console():
    try:
        splash_screen.display_splash_screen()
        clear_screen.clear()
        show_banner.banner()
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            cleanup_and_exit.cleanup()
    except KeyboardInterrupt:
        cleanup_and_exit.cleanup()
    while True:
        try:
            cfg.blacklisted_ip = list(set(cfg.blacklisted_ip))
            cfg.whitelisted_ip = list(set(cfg.whitelisted_ip))
            command_input = raw_input(cfg.prompt_default).strip()
            option = command_input.split(' ',1)[0]
            if option == 'banner':
                show_banner.banner()
            elif option == 'clear':
                clear_screen.clear()
            elif option == 'help':
                print cfg.main_help_menu
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
            elif option in ('add','rm'):
                set_globals.set_global_variables(command_input)
            elif option == 'change':
                change_session_values.change_values(command_input)
            elif option == 'fake':
                try:
                    new_fake_reply = command_input.split(' ',1)[1]
                except IndexError:
                    print cfg.err + 'Provide a fake reply'
                cfg.fake_reply = new_fake_reply
                print cfg.pos + 'Changed server fake reply'
            elif option == 'listeners':
                print cfg.pos + 'Switching...'
                listener_handler.listener_handler_console()
            elif option == 'scouts':
                print cfg.pos + 'Switching...'
                scout_handler.scout_console()
            elif option == 'generator':
                print cfg.pos + 'Switching...'
                generator_handler.generator_handler_console()
            elif option == 'show':
                print '\n' + cfg.note + 'Whitelisted IPs : ' + ', '.join(cfg.whitelisted_ip)
                print '\n' + cfg.note + 'Blacklisted IPs : ' + ', '.join(cfg.blacklisted_ip)
                print '\n' + cfg.note + 'Current default listener key : ' + cfg.listener_key
                print '\n' + cfg.note + 'Current default scout key : ' + cfg.scout_key
                print '\n' + cfg.note + 'Current listener fake reply : ' + cfg.fake_reply + '\n'
            elif option == 'reset':
                try:
                    option = command_input.split(' ')[1]
                    if option == 'wlist':
                        cfg.whitelisted_ip = []
                        print cfg.pos + 'reset value'
                    elif option == 'blist':
                        cfg.blacklisted_ip = []
                        print cfg.pos + 'reset value'
                    elif option == 'key':
                        cfg.listener_key = cfg.untouched_server_key
                        print cfg.pos + 'reset value'
                    elif option == 'sid':
                        cfg.scout_key = cfg.untouched_scout_identifier
                        print cfg.pos + 'reset value'
                    elif option == 'fake_reply':
                        cfg.fake_reply = 'Socket Server Running'
                        print cfg.pos + 'reset value'
                    elif option == 'all':
                        cfg.whitelisted_ip,cfg.blacklisted_ip = [],[]
                        cfg.listener_key,cfg.scout_key = cfg.untouched_server_key,cfg.untouched_scout_identifier
                        cfg.fake_reply = 'Socket Server Running'
                        print cfg.pos + 'reset all'
                    else:
                        raise IndexError
                except IndexError:
                    print cfg.err + 'Invalid command syntax/command arguments'
            elif option == '':
                pass
            else:
                print cfg.err + 'Unknown command "' + command_input + '", run "help" for help menu'
        except EOFError:
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                cleanup_and_exit.cleanup()
        except KeyboardInterrupt:
            cleanup_and_exit.cleanup()
        #except Exception as e:
        #    print cfg.err + 'Error : ' + str(e)
