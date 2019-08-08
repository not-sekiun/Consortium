import os
import collections
import library.modules.get_all_modules as get_all_modules
import library.modules.get_private_ip as get_private_ip


def main():
    started_at = os.getcwd()
    try:
        with open('resources/PyIris.cred', 'r') as f:
            key = f.read()
    except IOError:
        pass
    private_ip = get_private_ip.main()
    listener_values = {'Interface': ['0.0.0.0', 'The local interface to start a listener'],
                       'Port': ['9999', 'The local port to start a listener'],
                       'Name': ['Listener', 'Name of the listener'],
                       'Reply': ['', 'The reply to send back in the case of a failed listener authentication/ connection']}
    scout_values = {'Host': [private_ip, 'The local hostname to connect back to (Reverse) or the interface to listen on (Bind). You can set multiple hostnames to connect back to by separating them with commas'],
                    'Port': ['9999', 'The local port to connect back on (Reverse) or the remote port to listen on (Bind)'],
                    'Timeout': ['5', 'The timeout value for the scout'],
                    'Windows': ['True', 'When "True", will generate a windows scout, else a linux scout'],
                    'Path': [os.path.join(started_at, 'generated', 'payload.py'),
                             'Path to generate payload python file to'],
                    'Compile': ['False',
                                'When "True", will compile scout to EXE (windows) or ELF (Linux), '
                                'else it will not compile']}
    incremented_listener_id = 0
    incremented_scout_id = 0
    listener_database = {}
    scout_database = {}
    black_list = []
    white_list = []
    win_components = collections.OrderedDict()
    tmp_counter = 0
    iterdir = list(get_all_modules.main(os.getcwd() + '/components/windows'))
    iterdir.sort()
    for i in iterdir:
        i = i.replace('\\', '/')
        if i.endswith('.py') and not i.endswith('__init__.py'):
            win_components[str(tmp_counter)] = i[len(os.getcwd() + '/components') + 1:][:-3]
            tmp_counter += 1
    lin_components = collections.OrderedDict()
    tmp_counter = 0
    iterdir = list(get_all_modules.main(os.getcwd() + '/components/linux'))
    iterdir.sort()
    for i in iterdir:
        i = i.replace('\\', '/')
        if i.endswith('.py') and not i.endswith('__init__.py'):
            lin_components[str(tmp_counter)] = i[len(os.getcwd() + '/components') + 1:][:-3]
            tmp_counter += 1
    encoders = collections.OrderedDict()
    tmp_counter = 0
    iterdir = list(get_all_modules.main(os.getcwd() + '/encoders'))
    iterdir.sort()
    for i in iterdir:
        i = i.replace('\\', '/')
        if i.endswith('.py') and not i.endswith('__init__.py'):
            encoders[str(tmp_counter)] = i[len(os.getcwd() + '/encoders') + 1:][:-3]
            tmp_counter += 1
    loaded_components = collections.OrderedDict()
    loaded_encoders = []
    import_statements = []
    functions = []
    logics = []
    global_objs = []
    startup = []
    startup_start = []
    startup_end = []
    win_base_to_use = 'windows/bases/reverse_tcp_base'
    lin_base_to_use = 'linux/bases/reverse_tcp_base'
    help_menu = {}
    if os.name == 'nt':
        generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92m' + \
                           '\x1b[1m\x1b[32mGenerator\x1b[0m' + \
                           '\x1b[1m\x1b[37m@\x1b[0m\033[92m' + \
                           '\x1b[1m\x1b[32mWindows\x1b[0m' + \
                           '\x1b[1m\x1b[37m) > \x1b[0m'
    else:
        generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92m' + \
                           '\x1b[1m\x1b[32mGenerator\x1b[0m' + \
                           '\x1b[1m\x1b[37m@\x1b[0m\033[92m' + \
                           '\x1b[1m\x1b[32mLinux\x1b[0m' + \
                           '\x1b[1m\x1b[37m) > \x1b[0m'
        scout_values['Windows'] = ['False', 'When "True", will generate a windows scout, else a linux scout']
    neg = '\x1b[1m\x1b[31m[-]\x1b[0m'
    pos = '\x1b[1m\x1b[32m[+]\x1b[0m'
    war = '\x1b[1m\x1b[33m[!]\x1b[0m'
    inf = '\x1b[1m\x1b[34m[*]\x1b[0m'
    pro = '\x1b[1m\x1b[35m[>]\x1b[0m'
    lod = '\x1b[1m\x1b[34m[...]\x1b[0m'
    globals().update(locals())
