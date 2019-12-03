import library.modules.config as config

config.main()


def main(command):
    try:
        id = command.split(' ', 1)[1]
        if id in list(config.listener_database.keys()):
            del (config.listener_database[id])
            print(config.inf + 'Sent kill message to listener of ID : ' + id + '...')
        elif id == 'all':
            print(config.inf + 'Sent kill message to all listeners')
            config.listener_database = {}
        else:
            print(config.neg + 'Listener of ID : ' + id + ' is not active')
    except IndexError:
        print(config.neg + 'Please specify the ID of the listener to kill, or specify "all"')
