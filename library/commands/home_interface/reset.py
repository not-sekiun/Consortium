import library.modules.config as config

config.main()

def main(command):
    try:
        list_type = command.split(' ')[1]
        if list_type == 'wh':
            config.white_list = []
            print config.pos + 'Reset whitelist'
        elif list_type == 'bl':
            config.black_list = []
            print config.pos + 'Reset blacklist'
        elif list_type == 'all':
            config.white_list = []
            config.black_list = []
            print config.pos + 'Reset all'
        else:
            raise IndexError
    except IndexError:
        print config.neg + 'Please specify a valid list to reset'
    except ValueError:
        print config.neg + 'Item user wants to reset does not exist'