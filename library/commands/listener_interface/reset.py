import library.modules.config as config

config.main()

def main(command):
    try:
        local_static_values = {'Interface':['0.0.0.0','The local interface to start a listener'],
                               'Port':['9999','The local port to start a listener'],
                               'Name':['Listener','Name of the listener']}
        option = command.split(' ',1)[1]
        if option in local_static_values:
            config.listener_values[option] = local_static_values[option]
            print '[+]Reset option : ' + option
        elif option == 'all':
            config.listener_values = {'Interface':['0.0.0.0','The local interface to start a listener'],
                                      'Port':['9999','The local port to start a listener'],
                                      'Name':['Listener','Name of the listener']}
            print '[+]Reset all options'
        else:
            print '[-]Please specify a valid option to reset'
    except IndexError:
        print '[-]Please specify a valid option to reset'