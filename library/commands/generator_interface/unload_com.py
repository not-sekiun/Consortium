import collections
import library.modules.config as config
import library.modules.key_from_val as key_from_val

config.main()


def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        if load_off == 'all':
            if config.scout_values['Windows'][0] == 'True':
                config.loaded_components = collections.OrderedDict()
                config.loaded_components['base'] = config.win_base_to_use
                print config.pos + 'Unloaded all loaded windows components'
            else:
                config.loaded_components = collections.OrderedDict()
                config.loaded_components['base'] = config.lin_base_to_use
                print config.pos + 'Unloaded all loaded linux components'
        else:
            if key_from_val.main(config.loaded_components, load_off) == 'base' or load_off == 'base':
                print config.war + 'Do not unload base components, loading another base component will automatically replaces the already loaded base components as there can only be one base components'
                raise KeyError
            try:
                name = config.loaded_components[load_off]
                del (config.loaded_components[load_off])
                print config.pos + 'Unloaded : ' + name
                return
            except KeyError:
                del (config.loaded_components[key_from_val.main(config.loaded_components, load_off)])
                print config.pos + 'Unloaded : ' + load_off
                return
            raise KeyError
    except (KeyError, IndexError):
        print config.neg + 'Please specify a valid component to unload or "all" to load all components. Note : "base" component cannot be unloaded'
