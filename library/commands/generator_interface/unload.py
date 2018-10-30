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
                config.loaded_components['-'] = 'windows/base'
                print config.pos + 'Unloaded all loaded windows components'
            else:
                config.loaded_components = collections.OrderedDict()
                config.loaded_components['-'] = 'linux/base'
                print config.pos + 'Unloaded all loaded linux components'
        else:
            if key_from_val.main(config.loaded_components, load_off) == '-' or load_off == '-':
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
    except KeyError:
        print config.neg + 'Please specify a valid component to unload or "all" to load all components. Note : the default component, */base cannot be unloaded'
