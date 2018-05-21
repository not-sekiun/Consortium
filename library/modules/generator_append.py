import library.modules.config as config

config.main()

def main():
    if config.scout_values['Windows'][0] == 'True':
        if 'linux/base' in config.loaded_components:
            config.loaded_components.remove('linux/base')
        config.loaded_components.append('windows/base')
        config.loaded_components = list(set(config.loaded_components))
    else:
        if 'windows/base' in config.loaded_components:
            config.loaded_components.remove('windows/base')
        config.loaded_components.append('linux/base')
        config.loaded_components = list(set(config.loaded_components))