import library.modules.config as config

config.main()

tmp_enc = config.encoders.values()
for i in tmp_enc:
    exec ('import encoders.' + i.replace('/', '.') + ' as ' + i.replace('/', '_'))
print config.pos + 'Loaded all encoders info - OK'


def main(command):
    try:
        load_on = command.split(' ', 1)[1]
        if load_on in config.encoders:
            load_on = config.encoders[load_on]
        else:
            if load_on in config.encoders.values():
                pass
            else:
                raise KeyError
        exec (load_on.replace('/', '_') + '.main("info")')
    except (IndexError, KeyError):
        print config.neg + 'Please specify a valid encoder to show more info for'