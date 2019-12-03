import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()

tmp_win = list(config.win_components.values())
for i in tmp_win:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print(config.pos + 'Loaded all windows components info - OK')
tmp_lin = list(config.lin_components.values())
for i in tmp_lin:
    exec ('import components.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print(config.pos + 'Loaded all linux components info - OK')


def more_com(load_on):
    if config.scout_values['Windows'][0] == 'True':
        sample_space = list(set(tmp_win + list(config.loaded_components.values())))
        if load_on in sample_space:
            exec (load_on.replace('/', '_') + '.main("info")')
        else:
            load_on = dict(list(config.win_components.items()) + list(config.loaded_components.items()))[load_on]
            exec (load_on.replace('/', '_') + '.main("info")')
    else:
        sample_space = list(set(tmp_lin + list(config.loaded_components.values())))
        if load_on in sample_space:
            exec (load_on.replace('/', '_') + '.main("info")')
        else:
            load_on = dict(list(config.lin_components.items()) + list(config.loaded_components.items()))[load_on]
            exec (load_on.replace('/', '_') + '.main("info")')


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        if load_on == 'all':
            sample_space = list(set(tmp_win + list(config.loaded_components.values())))
            for i in sample_space:
                if i in sample_space:
                    exec (i.replace('/', '_') + '.main("info")')
                else:
                    i = dict(list(config.win_components.items()) + list(config.loaded_components.items()))[
                        i]
                    exec (i.replace('/', '_') + '.main("info")')
        else:
            load_on = generator_id_parser.main(load_on, 'components', None)
            load_on = list(map(str, load_on))
            for i in load_on:
                more_com(str(i))
    except (IndexError, KeyError):
        print(config.neg + 'Please specify a valid component to show more info for')
