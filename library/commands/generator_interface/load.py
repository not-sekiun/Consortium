import library.modules.config as config

config.main()

def main(command):
    try:
        load_on = command.split(' ',1)[1]
        if load_on in config.win_components or load_on in config.lin_components:
            config.loaded_components.append(load_on)
            print '[+]Loaded : ' + load_on
        else:
            raise IndexError
    except IndexError:
        print '[-]Please specify a valid component to load'