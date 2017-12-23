import time
import modules.cfg as cfg
import modules.randomized_output as randomized_output

cfg.global_variables()

def change_values(command):
    try:
        type_of_value = command.split(' ')[1]
        new_value = command.split(' ')[2]
        if type_of_value == 'lkey':
            if new_value == 'rand':
                new_value = randomized_output.rand_string(50)
            cfg.listener_key = new_value
            print cfg.pos + 'Changed ' + type_of_value + ' to : ' + new_value
        elif type_of_value == 'skey':
            confirmation = raw_input(cfg.user_in + 'Are you sure you want to change this sessions scout key [y/n] : ')
            if confirmation == 'y':
                if new_value == 'rand':
                    new_value = randomized_output.rand_string(50)
                cfg.scout_key = new_value
                print cfg.pos + 'Changed ' + type_of_value + ' to : ' + new_value
            elif confirmation == 'n':
                print cfg.note + 'Aborted changing of scout identifier value'
                return
            else:
                return
        else:
            raise IndexError
    except IndexError:
        print cfg.err + 'Invalid command syntax/command arguments'
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '\n' + cfg.note + 'Aborted changing of values'
    except KeyboardInterrupt:
            print '\n' + cfg.note + 'Aborted changing of values'
