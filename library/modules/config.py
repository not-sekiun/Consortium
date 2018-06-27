import os

def main():
    started_at = os.getcwd()
    try:
        f = open('PyIris.cred')
        key = f.read()
        f.close()
    except:
        pass
    listener_values = {'Interface':['0.0.0.0','The local interface to start a listener'],
                       'Port':['9999','The local port to start a listener'],
                       'Name':['Listener','Name of the listener'],}
    scout_values = {'Host':['127.0.0.1','The local hostname to connect back to'],
                    'Port':['9999','The local port to connect back on'],
                    'Timeout':['5','The timeout value for the scout'],
                    'Windows':['True','When "True", will generate a windows scout, else a linux scout'],
                    'Path':[os.path.join(started_at, 'payload.py'),'Path to generate payload to']}
    incremented_listener_id = 0
    incremented_scout_id = 0
    listener_database = {}
    scout_database = {}
    black_list = []
    white_list = []
    win_components = []
    for i in os.listdir(os.getcwd() + '/components/windows'):
        if i.endswith('.py') and i != '__init__.py' and i != 'base.py':
            win_components.append('windows/' + i[:-3])
    lin_components = []
    for i in os.listdir(os.getcwd() + '/components/linux'):
        if i.endswith('.py') and i != '__init__.py' and i != 'base.py':
            lin_components.append('linux/' + i[:-3])
    loaded_components = []
    import_statements = []
    functions = []
    logics = []



    #GUI variables
    max_cmp_title=0

    globals().update(locals())