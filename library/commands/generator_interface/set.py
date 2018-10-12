import library.modules.config as config

config.main()

def main(command):
    try:
        config.scout_values[command.split(' ')[1]][0] = command.split(' ', 2)[2]
        print '[+]Set "' + command.split(' ')[1] + '" to "' + command.split(' ', 2)[2] + '"'
        if config.scout_values['Windows'][0] == 'True':
            config.generator_prompt = 'PyIris (Generator@Windows) > '
        else:
            config.generator_prompt = 'PyIris (Generator@Linux) > '
    except (IndexError, KeyError):
        print '[-]Please specify a valid option and value'