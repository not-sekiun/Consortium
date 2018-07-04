import library.modules.config as config

config.main()

def main(command):
    try:
        list_type = command.split(' ')[1]
        if list_type == 'wh':
            config.white_list = []
            print '[+]Reset whitelist'
        elif list_type == 'bl':
            config.black_list = []
            print '[+]Reset blacklist'
        elif list_type == 'all':
            config.white_list = []
            config.black_list = []
            print '[+]Reset all'
        else:
            raise IndexError
    except IndexError:
        print '[-]Please specify a valid list to reset'
    except ValueError:
        print '[-]Item user wants to reset does not exist'