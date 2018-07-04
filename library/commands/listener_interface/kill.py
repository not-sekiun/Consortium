import time
import library.modules.config as config

config.main()

def main(command):
    try:
        id = command.split(' ',1)[1]
        if id in config.listener_database.keys():
            del(config.listener_database[id])
            print '[*]Sent kill message to listener of ID : ' + id + '...'
        elif id == 'all':
            print '[*]Sent kill message to all listeners'
            config.listener_database = {}
        else:
            print '[-]Listener of ID : ' + id + ' is not active'
    except IndexError:
        print '[-]Please specify the ID of the listener to kill, or specify "all"'