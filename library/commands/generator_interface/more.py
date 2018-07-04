import library.modules.config as config

config.main()

tmp_win = config.win_components
tmp_win.append('windows/base')
for i in tmp_win:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all windows components info - OK'
tmp_lin = config.lin_components
tmp_lin.append('linux/base')
for i in tmp_lin:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print '[+]Loaded all linux components info - OK'

def main(command):
    try:
        load_on = command.split(' ',1)[1]
        if load_on in tmp_win or load_on in tmp_lin:
            exec (load_on.replace('/', '_') + '.main("info")')
        else:
            raise IndexError
    except IndexError:
        print '[-]Please specify a valid component to show more info for'