import library.modules.config as config

config.main()

def main(command):
    try:
        if command.split(' ',1)[1] == 'all':
            keys = config.listener_database.keys()
            keys.sort()
            for i in keys:
                info = config.listener_database[i]
                print '[*]Advanced Info for : ' + i
                print '\n   ID            : ' + i
                print '   Interface     : ' + info[0]
                print '   Port          : ' + info[1]
                print '   Assigned Name : ' + info[2]
                print '   Started on    : ' + info[3]
                print '\n'
        else:
            info = config.listener_database[command.split(' ',1)[1]]
            print '[*]Advanced Info : '
            print '\n   ID            : ' + command.split(' ',1)[1]
            print '   Interface     : ' + info[0]
            print '   Port          : ' + str(info[1])
            print '   Assigned Name : ' + info[2]
            print '   Started on    : ' + info[3]
            print '\n'
    except (IndexError, KeyError):
        print '[-]Please specify a valid listener ID to show more info for'