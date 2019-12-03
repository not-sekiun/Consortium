import library.modules.config as config

config.main()


def main(command):
    try:
        list_type = command.split(' ')[1]
        hostname = command.split(' ', 2)[2]
        if list_type == 'wh':
            config.white_list.append(hostname)
            config.white_list = list(set(config.white_list))
            print(config.pos + 'Added to whitelist')
        elif list_type == 'bl':
            config.black_list.append(hostname)
            config.black_list = list(set(config.black_list))
            print(config.pos + 'Added to blacklist')
        else:
            raise IndexError
    except IndexError:
        print(config.neg + 'Please specify a valid list and a hostname to add to the list')
