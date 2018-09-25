import os
import library.modules.get_all_modules as get_all_modules


def main():
    started_at = os.getcwd()
    try:
        f = open('PyIris.cred')
        key = f.read()
        f.close()
    except:
        pass
    listener_values = {'Interface': ['0.0.0.0', 'The local interface to start a listener'],
                       'Port': ['9999', 'The local port to start a listener'],
                       'Name': ['Listener', 'Name of the listener'], }
    scout_values = {'Host': ['127.0.0.1', 'The local hostname to connect back to'],
                    'Port': ['9999', 'The local port to connect back on'],
                    'Timeout': ['5', 'The timeout value for the scout'],
                    'Windows': ['True', 'When "True", will generate a windows scout, else a linux scout'],
                    'Path': [os.path.join(started_at, 'payload.py'), 'Path to generate payload to'],
                    'Compile': ['False', 'When "True", will compile scout to EXE (windows) or ELF (Linux), else it will not compile']}
    incremented_listener_id = 0
    incremented_scout_id = 0
    listener_database = {}
    scout_database = {}
    black_list = []
    white_list = []
    win_components = []
    for i in list(get_all_modules.main(os.getcwd() + '/components/windows')):
        i = i.replace('\\', '/')
        if i.endswith('.py') and not i.endswith('__init__.py') and not i.endswith('base.py'):
            win_components.append(i[len(os.getcwd() + '/components') + 1:][:-3])
    lin_components = []
    for i in list(get_all_modules.main(os.getcwd() + '/components/linux')):
        i = i.replace('\\', '/')
        if i.endswith('.py') and not i.endswith('__init__.py') and not i.endswith('base.py'):
            lin_components.append(i[len(os.getcwd() + '/components') + 1:][:-3])
    loaded_components = []
    import_statements = []
    functions = []
    logics = []
    global_vars = []
    globals().update(locals())
