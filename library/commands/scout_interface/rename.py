import library.modules.config as config

config.main()

def main(command):
    try:
        id = command.split(' ',2)[1]
        new_name = command.split(' ',2)[2]
        config.scout_database[id][4] = new_name
        print config.pos + 'Successfully renamed scout'
    except (IndexError,KeyError):
        print config.neg + 'Please specify valid values, a valid ID and new name'