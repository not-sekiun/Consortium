import library.modules.config as config

config.main()

def main(command):
    try:
        if command.split(' ',1)[1] == 'all':
            keys = config.scout_database.keys()
            keys.sort()
            for i in keys:
                info = config.scout_database[i]
                print config.inf + 'Advanced Info for : ' + i
                print '\n   Connection Object : ' + str(info[0])
                print '   Remote Scout Host : ' + info[1]
                print '   Remote Scout Port : ' + info[2]
                print '   Connected through : ' + info[3]
                print '   Name              : ' + info[4]
                print '   Connected at      : ' + info[5]
                print '   Connection Type   : ' + info[6]
                print '\n'
        else:
            info = config.scout_database[command.split(' ',1)[1]]
            print config.inf + 'Advanced Info for : ' + command.split(' ',1)[1]
            print '\n   Socket Object     : ' + str(info[0])
            print '   Remote Scout Host : ' + info[1]
            print '   Remote Scout Port : ' + info[2]
            print '   Connected through : ' + info[3]
            print '   Name              : ' + info[4]
            print '   Connected at      : ' + info[5]
            print '   Connection Type   : ' + info[6]
            print '\n'
    except (IndexError, KeyError):
        print config.neg + 'Please specify a valid listener ID to show more info for'