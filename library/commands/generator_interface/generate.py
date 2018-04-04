import library.modules.config as config

config.main()

tmp_win = config.win_components
tmp_win.append('windows/base_component')
for i in tmp_win:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all windows components - OK'
tmp_lin = config.lin_components
tmp_lin.append('linux/base_component')
for i in tmp_lin:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all linux components - OK'

def main():
    if config.scout_values['Windows'][0] == 'True':
        print '[+]Filtering out invalid components (Filtering out linux/* components)...'
        load_on = [i for i in config.loaded_components if i.startswith('windows/')]
        load_on.append('windows/base_component')
        for i in load_on:
            print '[+]Loaded : ' + i
            exec(i.replace('/', '_') + '.main()')
        print '[*]Finished generating scout'
    else:
        print '[+]Filtering out invalid components (Filtering out windows/* components)...'
        load_on = [i for i in config.loaded_components if not i.startswith('windows/')]
        load_on.append('linux/base_component')
        for i in load_on:
            print '[+]Loaded : ' + i
            exec (i.replace('/', '_') + '.main()')
        print '[*]Finished generating scout'