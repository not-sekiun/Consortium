import library.modules.config as config
import library.modules.clean_import_data as clean_import_data

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
    print '[*]Reading contents from temporary written file...'
    f = open(config.scout_values['Path'][0], 'r')
    save_data = f.read()
    f.close()
    config.functions = list(set(config.functions))
    config.import_statements = list(set(config.import_statements))
    config.global_vars = list(set(config.global_vars))
    config.logics = list(set(config.logics))
    f = open(config.scout_values['Path'][0], 'w')
    print '[*]Writing in imports...'
    f.write(clean_import_data.main(config.import_statements) + '\n\n')
    print '[*]Writing in global variables...'
    for i in config.global_vars:
        f.write(i + '\n')
    print '[*]Writing in functions...'
    for i in config.functions:
        f.write(i + '\n')
    print '[*]Writing in base component...'
    for i in config.logics:
        save_data = save_data.replace('#Statements#', '#Statements#' + i)
    save_data = save_data.replace('#Statements#', '')
    f.write(save_data)
    f.close()
    print '[+]Finished generating scout'
    config.functions = []
    config.import_statements = []
    config.global_vars = []
    config.logics = []
