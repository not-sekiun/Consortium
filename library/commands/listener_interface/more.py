import library.modules.config as config

config.main()


def main(command):
    try:
        if command.split(' ', 1)[1] == 'all':
            keys = list(config.listener_database.keys())
            keys.sort()
            for i in keys:
                info = config.listener_database[i]
                print(config.inf + 'Advanced Info for : ' + i)
                print('\n   ID                       : ' + i)
                print('   Interface                : ' + info[0])
                print('   Port                     : ' + str(info[1]))
                print('   Assigned Name            : ' + info[2])
                print('   Started on               : ' + info[3])
                print('   Scout connection history : ')
                for scout_history in info[4]:
                    print ('    - ' + scout_history)
                print('\n')
        else:
            info = config.listener_database[command.split(' ', 1)[1]]
            print(config.inf + 'Advanced Info : ')
            print('\n   ID                       : ' + command.split(' ', 1)[1])
            print('   Interface                : ' + info[0])
            print('   Port                     : ' + str(info[1]))
            print('   Assigned Name            : ' + info[2])
            print('   Started on               : ' + info[3])
            print('   Scout connection history : ')
            for scout_history in info[4]:
                print('    - ' + scout_history)
            print('\n')
    except (IndexError, KeyError):
        print(config.neg + 'Please specify a valid listener ID to show more info for')
