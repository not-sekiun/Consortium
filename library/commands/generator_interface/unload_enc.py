import library.modules.config as config
import library.modules.generator_id_parser as generator_id_parser
from collections import OrderedDict

config.main()


def unload_enc(load_off, loaded_encoders):
    if load_off == 'all':
        loaded_encoders = {}
        print config.pos + 'Unloaded all encoders'
    elif load_off in loaded_encoders.values():
        found = False
        for key, val in loaded_encoders.items():
            if val == load_off:
                del(loaded_encoders[key])
                print config.pos + 'Unloaded : ' + load_off
                found = True
                break
        if not found:
            raise KeyError
    else:
        print config.pos + 'Unloaded : ' + loaded_encoders[load_off]
        del (loaded_encoders[load_off])
    return loaded_encoders


def main(command):
    try:
        load_off = command.split(' ', 1)[1]
        load_off = generator_id_parser.main(load_off, 'encoders', 'unload')
        load_off = map(str, load_off)
        snapshot = config.loaded_encoders
        snapshot_dict = OrderedDict()
        for i in range(len(snapshot)):
            snapshot_dict[str(i)] = snapshot[i]
        for i in load_off:
            print config.inf + 'Unloading : ' + i
            snapshot_dict = unload_enc(str(i), snapshot_dict)
        config.loaded_encoders = snapshot_dict.values()
    except (KeyError, IndexError, TypeError):
        print config.neg + 'Please specify a valid encoder to unload'
