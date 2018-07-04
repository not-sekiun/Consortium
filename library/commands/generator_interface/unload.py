import library.modules.config as config

config.main()

def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        if load_off.endswith('/base'):
            print '[*]Can\'t unload the default base component'
        else:
            config.loaded_components.remove(load_off)
            print '[+]Unloaded : ' + load_off
    except (IndexError, ValueError):
        print '[-]Please specify a valid component to unload, note : the default loaded library cannot be unloaded'