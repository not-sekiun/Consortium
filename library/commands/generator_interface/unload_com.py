import collections
import library.modules.config as config
import library.modules.key_from_val as key_from_val
import library.modules.generator_id_parser as generator_id_parser

config.main()


def unload_com(load_off):
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
        if load_off == 'base' or key_from_val.main(config.loaded_components, load_off) == 'base':
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


def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        load_off = generator_id_parser.main(load_off, operation='unload')
        load_off = map(str, load_off)
        for i in load_off:
            print config.inf + 'Unloading : ' + str(i)
            unload_com(str(i))
    except (KeyError, IndexError):
        print config.neg + 'Please specify a valid component to unload or "all" to load all components. \x1b[1m\x1b[31mNote : "base" component cannot be unloaded\x1b[0m'
