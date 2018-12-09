import library.modules.sort_dictionary_by_int_val as sort_dictionary_by_int_val
import collections
import library.modules.config as config

config.main()


def main():
    if config.scout_values['Windows'][0] == 'True':
        config.loaded_components['base'] = config.win_base_to_use
        config.loaded_components = sort_dictionary_by_int_val.main(config.loaded_components)
        for i in config.loaded_components.values():
            if i.startswith('linux/'):
                config.loaded_components = collections.OrderedDict()
                config.loaded_components['base'] = config.win_base_to_use
                return
    else:
        config.loaded_components['base'] = config.lin_base_to_use
        config.loaded_components = sort_dictionary_by_int_val.main(config.loaded_components)
        for i in config.loaded_components.values():
            if i.startswith('windows/'):
                config.loaded_components = collections.OrderedDict()
                config.loaded_components['base'] = config.lin_base_to_use
                return
