import library.modules.config as config

config.main()
tmp_win = config.win_components
tmp_win.append('windows/base')
for i in tmp_win:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all windows components into generator - OK'
tmp_lin = config.lin_components
tmp_lin.append('linux/base')
for i in tmp_lin:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all linux components into generator - OK'


def main():
    for i in config.loaded_components:
        print '[+]Loading and executing : ' + i
        exec (i.replace('/', '_') + '.main("generate")')
    print '[*]Reading contents from written file...'
    f = open(config.scout_values['Path'][0], 'r')
    save_data = f.read()
    f.close()
    f = open(config.scout_values['Path'][0], 'w')
    print '[*]Writing in imports...'
    for i in config.import_statements:
        f.write(i + '\n')
    print '[*]Writing in global varibals'
    for i in config.global_vars:
        f.write(i + '\n')
    print '[*]Writing in functions...'
    for i in config.functions:
        f.write(i + '\n')
    print '[*]Writing in base component'
    for i in config.logics:
        save_data = save_data.replace('#Statements#', '#Statements#\n' + i)
    save_data = save_data.replace('#Statements#\n', '')
    f.write(save_data)
    f.close()
    print '[*]Finished generating scout'
    config.functions = []
    config.import_statements = []
    config.global_vars = []
    config.logics = []
