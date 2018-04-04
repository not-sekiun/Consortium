import library.modules.config as config

config.main()

def main(command):
    try:
        config.listener_values[command.split(' ')[1]][0] = command.split(' ', 2)[2]
        print '[+]Set "' + command.split(' ')[1] + '" to "' + command.split(' ', 2)[2] + '"'
    except (IndexError, KeyError):
        print '[-]Please specify a valid option and value'