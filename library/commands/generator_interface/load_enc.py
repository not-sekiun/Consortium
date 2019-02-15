import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()


def load_enc(load_on):
    id = load_on
    if load_on in config.encoders:
        load_on = config.encoders[load_on]
    else:
        if load_on in config.encoders.values():
            pass
        else:
            raise KeyError
    print config.pos + 'Loaded : ' + load_on + ' (' + id + ')'
    config.loaded_encoders.append(load_on)


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        load_on = generator_id_parser.main(load_on, 'encoders')
        load_on = map(str, load_on)
        if type(load_on) == list:
            for i in load_on:
                load_enc(str(i))
        else:
            print load_on
    except (KeyError, IndexError):
        print config.neg + 'Please specify a valid encoder to load'
