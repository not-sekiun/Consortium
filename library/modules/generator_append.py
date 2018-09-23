import library.modules.config as config

config.main()

def main():
    if config.scout_values['Windows'][0] == 'True':
        config.loaded_components.append('windows/base')
        config.loaded_components = list(set(config.loaded_components))
        for i in config.loaded_components:
            if i.startswith('linux/'):
                config.loaded_components = []
                config.loaded_components.append('windows/base')
                return
    else:
        config.loaded_components.append('linux/base')
        config.loaded_components = list(set(config.loaded_components))
        for i in config.loaded_components:
            if i.startswith('windows/'):
                config.loaded_components = []
                config.loaded_components.append('linux/base')
                return
