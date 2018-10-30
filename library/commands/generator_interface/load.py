import library.modules.key_from_val as key_from_val
import library.modules.config as config

config.main()


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        if load_on == 'all':
            if config.scout_values['Windows'][0] == 'True':
                for i in config.win_components.values():
                    config.loaded_components[key_from_val.main(config.win_components, i)] = i
                    print config.pos + 'Loaded : ' + i
                print config.pos + 'Loaded all windows components'
            else:
                for i in config.lin_components.values():
                    config.loaded_components[key_from_val.main(config.lin_components, i)] = i
                    print config.pos + 'Loaded : ' + i
                print config.pos + 'Loaded all linux components'
        else:
            if config.scout_values['Windows'][0] == 'True':
                if load_on in config.win_components.keys():
                    load_on = config.win_components[load_on]
                if load_on in config.loaded_components.values():
                    print config.neg + 'Component already loaded'
                else:
                    id = key_from_val.main(config.win_components, load_on)
                    if not id:
                        raise KeyError
                    config.loaded_components[id] = load_on
                    print config.pos + 'Loaded : ' + load_on
            else:
                if load_on in config.lin_components.keys():
                    load_on = config.lin_components[load_on]
                if load_on in config.loaded_components.values():
                    print config.neg + 'Component already loaded'
                else:
                    id = key_from_val.main(config.lin_components, load_on)
                    if not id:
                        raise KeyError
                    config.loaded_components[id] = load_on
                    print config.pos + 'Loaded : ' + load_on
    except KeyError:
        print config.neg + 'Please specify a valid component to load or "all" to load all components. Note : the default component, */base is loaded by default'
