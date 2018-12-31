import library.modules.config as config

config.main()


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
        print config.pos + 'Loaded : ' + load_on
        config.loaded_encoders.append(load_on)
    except (KeyError, IndexError):
        print config.neg + 'Please specify a valid encoder to load'
