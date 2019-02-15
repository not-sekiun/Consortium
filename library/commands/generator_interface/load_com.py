import library.modules.key_from_val as key_from_val
import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()


def load_com(load_on):
    id = load_on
    if config.scout_values['Windows'][0] == 'True':
        if load_on in config.win_components.keys():
            if config.win_components[load_on].startswith('windows/bases/') and config.win_components[load_on] not in config.loaded_components.values():
                config.win_base_to_use = config.win_components[load_on]
                print config.pos + 'Replaced the loaded on base with new base : ' + config.win_components[
                    load_on] + ' (' + id + ')'
                return
            else:
                load_on = config.win_components[load_on]
        if load_on in config.loaded_components.values():
            print config.neg + 'Component already loaded' + ' (' + id + ')'
        else:
            id = key_from_val.main(config.win_components, load_on)
            if not id:
                raise KeyError
            if load_on.startswith('windows/bases/'):
                config.win_base_to_use = load_on
                print config.pos + 'Replaced the loaded on base with new base : ' + load_on + ' (' + id + ')'
                return
            else:
                config.loaded_components[id] = load_on
            print config.pos + 'Loaded : ' + load_on + ' (' + id + ')'
    else:
        if load_on in config.lin_components.keys():
            if config.lin_components[load_on].startswith('linux/bases/') and config.lin_components[load_on] not in config.loaded_components.values():
                config.lin_base_to_use = config.lin_components[load_on]
                print config.pos + 'Replaced the loaded on base with new base : ' + config.lin_components[
                    load_on] + ' (' + id + ')'
                return
            else:
                load_on = config.lin_components[load_on]
        if load_on in config.loaded_components.values():
            print config.neg + 'Component already loaded' + ' (' + id + ')'
        else:
            id = key_from_val.main(config.lin_components, load_on)
            if not id:
                raise KeyError
            if load_on.startswith('linux/bases/'):
                config.win_base_to_use = load_on
                print config.pos + 'Replaced the loaded on base with new base : ' + load_on + ' (' + id + ')'
                return
            config.loaded_components[id] = load_on
            print config.pos + 'Loaded : ' + load_on + ' (' + id + ')'


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        load_on = generator_id_parser.main(load_on)
        load_on = map(str, load_on)
        if type(load_on) == list:
            for i in load_on:
                load_com(str(i))
        else:
            print load_on
    except (KeyError, IndexError):
        print config.neg + 'Please specify a valid component to load or "all" to load all components. Note : the default component, */base is loaded by default'
