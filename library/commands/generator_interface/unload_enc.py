import library.modules.config as config

config.main()


def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        if load_off == 'all':
            config.loaded_encoders = []
            print config.pos + 'Unloaded all encoders'
        elif load_off in config.loaded_encoders:
            config.loaded_encoders.remove(load_off)
            print config.pos + 'Unloaded : ' + load_off
        else:
            print config.pos + 'Unloaded : ' + config.loaded_encoders[int(load_off)]
            config.loaded_encoders.pop(int(load_off))
    except (KeyError, IndexError, TypeError):
        print config.neg + 'Please specify a valid encoder to unload'
