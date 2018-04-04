import library.modules.config as config

config.main()

def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        config.loaded_components.remove(load_off)
        print '[+]Unloaded : ' + load_off
    except (IndexError, ValueError):
        print '[-]Please specify a valid component to load'