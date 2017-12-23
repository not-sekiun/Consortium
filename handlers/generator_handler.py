import os
import time
import modules.cfg as cfg
import modules.show_banner as show_banner
import modules.clear_screen as clear_screen
import modules.execute_local_command as execute_local_command
import modules.cleanup_and_exit as cleanup_and_exit
import modules.generate_payload_with_template as generate_payload_with_template

cfg.global_variables()

def generator_handler_console():
    set_for = ''
    scout_default_values = {'Hostname': ['127.0.0.1', 'Host address to connect back to'],
                               'Port': [9999, 'Host port to connect back on'],
                               'Key': [cfg.listener_key, 'Listener key to be sent to listener in order to gain access'],
                            'SleepTime':['5','Duration for scout to sleep if it cannot connect to listener']}
    while True:
        try:
            if not set_for:
                command_input = raw_input(cfg.prompt_generator).strip()
            else:
                command_input = raw_input('\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[32mGenerator\x1b[0m \x1b[1m\x1b[37m:\x1b[0m \x1b[1m\x1b[32m' + set_for + '\x1b[0m\x1b[1m\x1b[37m) > \x1b[0m').strip()
            option = command_input.split(' ')[0]
            if option == 'banner':
                show_banner.banner()
            elif option == 'clear':
                clear_screen.clear()
            elif option == 'help':
                print cfg.generator_help_menu
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
                if not set_for:
                    print cfg.err + 'No payload has been chosen yet, run the "use" command'
                else:
                    print cfg.note + 'Setting for : ' + set_for
                config = [['    Option', 'Value', 'Information'], ['    ======', '=====', '===========']]
                for o, v in scout_default_values.items():
                    config.append(['    ' + o, str(v[0]), v[1]])
                print '\n'
                l = [len(max(i, key=len)) for i in zip(*config)]
                print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                                for item in config)) + '\n'
            elif option == 'set':
                try:
                    scout_default_values[command_input.split(' ')[1]][0] = command_input.split(' ',2)[2]
                    print cfg.pos + 'Set ' + command_input.split(' ')[1] + ' to ' + command_input.split(' ',2)[2]
                except (IndexError,KeyError):
                    print cfg.err + 'Invalid syntax, specify valid option and value'
            elif option == 'show':
                for i in cfg.payload_templates_list:
                    print i
            elif option == 'reset':
                scout_default_values = {'Hostname': ['127.0.0.1', 'Host address to connect back to'],
                                        'Port': [9999, 'Host port to connect back on'],
                                        'Key': [cfg.listener_key,
                                                'Listener key to be sent to listener in order to gain access'],
                                        'SleepTime': ['5',
                                                      'Duration for scout to sleep if it cannot connect to listener']}
                print cfg.pos + 'Reset all values'
            elif option == 'use':
                try:
                    payload_type = command_input.split(' ')[1]
                    if payload_type in cfg.payload_templates_list:
                        set_for = payload_type
                        print cfg.pos + 'Set payload to : ' + set_for
                    else:
                        raise IndexError
                except IndexError:
                    print cfg.err + 'Invalid payload, run "show" to see all payloads'
            elif option == 'generate':
                folder = None
                try:
                    folder = command_input.split(' ',1)[1]
                except IndexError:
                    pass
                if not set_for:
                    print cfg.err + 'Cannot generate, no payload set, run "use"'
                    continue
                generate_payload_with_template.generate_payload(set_for,scout_default_values,folder)
            elif option == '':
                pass
            else:
                print cfg.err + 'Unknown command "' + command_input + '", run "help" for help menu'
        except EOFError:
            time.sleep(2)
        except Exception as e:
            print cfg.err + 'Error : ' + str(e)