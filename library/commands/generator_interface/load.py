import library.modules.key_from_val as key_from_val
import library.modules.config as config

config.main()


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        if load_on == 'all':
            if config.scout_values['Windows'][0] == 'True':
                for i in [i for i in config.win_components.values() if not i.startswith('windows/bases/')]:
                    config.loaded_components[key_from_val.main(config.win_components, i)] = i
                    print config.pos + 'Loaded : ' + i
                print config.pos + 'Loaded all windows components'
            else:
                for i in [i for i in config.lin_components.values() if not i.startswith('linux/bases/')]:
                    config.loaded_components[key_from_val.main(config.lin_components, i)] = i
                    print config.pos + 'Loaded : ' + i
                print config.pos + 'Loaded all linux components'
        else:
            if config.scout_values['Windows'][0] == 'True':
                if load_on in config.win_components.keys():
                    if config.win_components[load_on].startswith('windows/bases/') and config.win_components[load_on] not in config.loaded_components.values():
                        config.win_base_to_use = config.win_components[load_on]
                        print config.pos + 'Replaced the loaded on base with new base : ' + config.win_components[
                            load_on]
                        return
                    else:
                        load_on = config.win_components[load_on]
                if load_on in config.loaded_components.values():
                    print config.neg + 'Component already loaded'
                else:
                    id = key_from_val.main(config.win_components, load_on)
                    if not id:
                        raise KeyError
                    if load_on.startswith('windows/bases/'):
                        config.win_base_to_use = load_on
                        print config.pos + 'Replaced the loaded on base with new base : ' + load_on
                        return
                    else:
                        config.loaded_components[id] = load_on
                    print config.pos + 'Loaded : ' + load_on
            else:
                if load_on in config.lin_components.keys():
                    if config.lin_components[load_on].startswith('linux/bases/') and config.lin_components[load_on] not in config.loaded_components.values():
                        config.lin_base_to_use = config.lin_components[load_on]
                        print config.pos + 'Replaced the loaded on base with new base : ' + config.lin_components[
                            load_on]
                        return
                    else:
                        load_on = config.lin_components[load_on]
                if load_on in config.loaded_components.values():
                    print config.neg + 'Component already loaded'
                else:
                    id = key_from_val.main(config.lin_components, load_on)
                    if not id:
                        raise KeyError
                    if load_on.startswith('linux/bases/'):
                        config.win_base_to_use = load_on
                        print config.pos + 'Replaced the loaded on base with new base : ' + load_on
                        return
                    config.loaded_components[id] = load_on
                    print config.pos + 'Loaded : ' + load_on
    except KeyError:
        print config.neg + 'Please specify a valid component to load or "all" to load all components. Note : the default component, */base is loaded by default'
