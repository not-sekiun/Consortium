import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()

tmp_win = config.win_components.values()
for i in tmp_win:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print config.pos + 'Loaded all windows components info - OK'
tmp_lin = config.lin_components.values()
for i in tmp_lin:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print config.pos + 'Loaded all linux components info - OK'


def more_com(load_on):
    if config.scout_values['Windows'][0] == 'True':
        sample_space = list(set(tmp_win + config.loaded_components.values()))
        if load_on in sample_space:
            exec (load_on.replace('/', '_') + '.main("info")')
        else:
            load_on = dict(config.win_components.items() + config.loaded_components.items())[load_on]
            exec (load_on.replace('/', '_') + '.main("info")')
    else:
        sample_space = list(set(tmp_lin + config.loaded_components.values()))
        if load_on in sample_space:
            exec (load_on.replace('/', '_') + '.main("info")')
        else:
            load_on = dict(config.lin_components.items() + config.loaded_components.items())[load_on]
            exec (load_on.replace('/', '_') + '.main("info")')


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        load_on = generator_id_parser.main(load_on)
        load_on = map(str, load_on)
        for i in load_on:
            more_com(str(i))
    except (IndexError, KeyError):
        print config.neg + 'Please specify a valid component to show more info for'
