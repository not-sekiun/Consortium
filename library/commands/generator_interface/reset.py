import library.modules.config as config

config.main()


def main(command):
    try:
        local_static_values = {'Host': ['127.0.0.1', 'The local hostname to connect back to'],
                               'Port': ['9999', 'The local port to connect back on'],
                               'Timeout': ['5', 'The timeout value for the scout'],
                               'Windows': ['True',
                                           'When "True", will generate a windows scout, else a linux scout'],
                               'Path': [config.started_at + '\payload.py', 'Path to generate payload to'],
                               'Compile': ['False', 'When "True", will compile scout to EXE (windows) or ELF (Linux), else it will not compile']}
        option = command.split(' ', 1)[1]
        if option in local_static_values:
            config.scout_values[option] = local_static_values[option]
            print '[+]Reset option : ' + option
        elif option == 'all':
            config.scout_values = {'Host': ['127.0.0.1', 'The local hostname to connect back to'],
                                   'Port': ['9999', 'The local port to connect back on'],
                                   'Timeout': ['5', 'The timeout value for the scout'],
                                   'Windows': ['True',
                                               'When "True", will generate a windows scout, else a linux scout'],
                                   'Path': [config.started_at + '\payload.py', 'Path to generate payload to'],
                                   'Compile': ['False',
                                               'When "True", will compile scout to EXE (windows) or ELF (Linux), else it will not compile']}
            print '[+]Reset all options'
        else:
            print '[-]Please specify a valid option to reset'
        if config.scout_values['Windows'][0] == 'True':
            config.generator_prompt = 'PyIris (Generator@Windows) > '
        else:
            config.generator_prompt = 'PyIris (Generator@Linux) > '
    except IndexError:
        print '[-]Please specify a valid option to reset'
