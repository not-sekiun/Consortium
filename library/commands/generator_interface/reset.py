import library.modules.config as config
import os

config.main()


def main(command):
    try:
        local_static_values = {'Host': [config.private_ip,
                                        'The local hostname to connect back to (Reverse) or the interface to listen on (Bind). You can set multiple hostnames to connect back to by separating them with commas'],
                               'Port': ['9999',
                                        'The local port to connect back on (Reverse) or the remote port to listen on (Bind)'],
                               'Timeout': ['5', 'The timeout value for the scout'],
                               'Windows': ['True', 'When "True", will generate a windows scout, else a linux scout'],
                               'Path': [os.path.join(config.started_at, 'generated', 'payload.py'),
                                        'Path to generate payload python file to'],
                               'Compile': ['False',
                                           'When "True", will compile scout to EXE (windows) or ELF (Linux), '
                                           'else it will not compile']}
        option = command.split(' ', 1)[1]
        if option in local_static_values:
            config.scout_values[option] = local_static_values[option]
            print(config.pos + 'Reset option : ' + option)
        elif option == 'all':
            config.scout_values = {'Host': [config.private_ip,
                                            'The local hostname to connect back to (Reverse) or the interface to listen on (Bind). You can set multiple hostnames to connect back to by separating them with commas'],
                                   'Port': ['9999',
                                            'The local port to connect back on (Reverse) or the remote port to listen on (Bind)'],
                                   'Timeout': ['5', 'The timeout value for the scout'],
                                   'Windows': ['True',
                                               'When "True", will generate a windows scout, else a linux scout'],
                                   'Path': [os.path.join(config.started_at, 'generated', 'payload.py'),
                                            'Path to generate payload python file to'],
                                   'Compile': ['False',
                                               'When "True", will compile scout to EXE (windows) or ELF (Linux), '
                                               'else it will not compile']}
            print(config.pos + 'Reset all options')
        else:
            print(config.neg + 'Please specify a valid option to reset')
        if config.scout_values['Windows'][0] == 'True':
            config.generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92m' + '\x1b[1m\x1b[32mGenerator\x1b[0m' + '\x1b[1m\x1b[37m@\x1b[0m\033[92m' + '\x1b[1m\x1b[32mWindows\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
        else:
            config.generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92m' + '\x1b[1m\x1b[32mGenerator\x1b[0m' + '\x1b[1m\x1b[37m@\x1b[0m\033[92m' + '\x1b[1m\x1b[32mLinux\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    except IndexError:
        print(config.neg + 'Please specify a valid option to reset')
