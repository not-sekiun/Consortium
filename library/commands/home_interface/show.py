import library.modules.config as config

config.main()


def main(command):
    try:
        list_type = command.split(' ', 1)[1]
        if list_type == 'wh':
            print('\n' + config.pos + 'Whitelisted hosts : ')
            for i in config.white_list:
                print('   ' + i)
            print('\n')
        elif list_type == 'bl':
            print('\n' + config.pos + 'Blacklisted hosts : ')
            for i in config.black_list:
                print('   ' + i)
            print('\n')
        elif list_type == 'all':
            print('\n' + config.pos + 'Whitelisted hosts : ')
            for i in config.white_list:
                print('   ' + i)
            print('\n' + config.pos + 'Blacklisted hosts : ')
            for i in config.black_list:
                print('   ' + i)
            print('\n')
        elif list_type == 'key':
            print(config.inf + 'Currently used key : \n   ' + config.key)
        else:
            raise IndexError
    except IndexError:
        print(config.neg + 'Please specify a valid object to show, ["wh"|"bl"|"all"|"key"]')
