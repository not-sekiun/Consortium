import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser

config.main()

tmp_enc = config.encoders.values()
for i in tmp_enc:
    exec ('import encoders.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print config.pos + 'Loaded all encoders info - OK'


def more_enc(load_on):
    if load_on in config.encoders:
        load_on = config.encoders[load_on]
    else:
        if load_on in config.encoders.values():
            pass
        else:
            raise KeyError
    exec (load_on.replace('/', '_') + '.main("info")')


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        load_on = generator_id_parser.main(load_on, 'encoders', None)
        load_on = map(str, load_on)
        for i in load_on:
            more_enc(str(i))
    except (IndexError, KeyError):
        print config.neg + 'Please specify a valid encoder to show more info for'
