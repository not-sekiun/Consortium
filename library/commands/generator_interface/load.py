import library.modules.config as config

config.main()


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        if load_on == 'all':
            if config.scout_values['Windows'][0] != 'True':
                config.loaded_components = []
                for i in config.lin_components:
                    config.loaded_components.append(i)
                    print '[+]Loaded : ' + i
                print '[+]Loaded all linux components'
            elif config.scout_values['Windows'][0] == 'True':
                config.loaded_components = []
                for i in config.win_components:
                    config.loaded_components.append(i)
                    print '[+]Loaded : ' + i
                print '[+]Loaded all windows components'
        else:
            if load_on.startswith('windows') and config.scout_values['Windows'][0] != 'True':
                print '[-]Can\'t load a windows module when scout is set to linux'
            elif load_on.startswith('linux') and config.scout_values['Windows'][0] == 'True':
                print '[-]Can\'t load a linux module when scout is set to windows'
            else:
                if load_on in config.win_components or load_on in config.lin_components:
                    if load_on in config.loaded_components:
                        print '[-]Component already loaded'
                    else:
                        config.loaded_components.append(load_on)
                        print '[+]Loaded : ' + load_on
                else:
                    raise IndexError
    except IndexError:
        print '[-]Please specify a valid component to load or "all" to load all components'
