import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()


def load_enc(load_on):
    if load_on in config.encoders:
        load_on = config.encoders[load_on]
    else:
        if load_on in list(config.encoders.values()):
            pass
        else:
            raise KeyError
    print(config.pos + 'Loaded : ' + load_on)
    config.loaded_encoders.append(load_on)


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        load_on = generator_id_parser.main(load_on, 'encoders', 'load')
        load_on = list(map(str, load_on))
        for i in load_on:
            print(config.inf + 'Loading : ' + i)
            load_enc(str(i))
    except (KeyError, IndexError):
        print(config.neg + 'Please specify a valid encoder to load')
