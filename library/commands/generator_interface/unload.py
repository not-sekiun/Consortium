import library.modules.config as config

config.main()


def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        if load_off.endswith('/base'):
            print '[*]Can\'t unload the default base component'
        else:
            if load_off == 'all':
                if config.scout_values['Windows'][0] != 'True':
                    config.loaded_components = ['linux/base']
                    print '[+]Unloaded all linux components'
                elif config.scout_values['Windows'][0] == 'True':
                    config.loaded_components = ['windows/base']
                    print '[+]Unloaded all windows components'
            else:
                config.loaded_components.remove(load_off)
                print '[+]Unloaded : ' + load_off
    except (IndexError, ValueError):
        print '[-]Please specify a valid component to unload or "all" to load all components. Note : the default loaded library cannot be unloaded'
