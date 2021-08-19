import library.modules.recv_all as recv_all
from ntpath import basename
from base64 import b64decode
import library.modules.config as config
import logging

config.main()


def main(sock):
    try:
        print(config.inf + 'Receiving data...')
        data = recv_all.main(sock).split(' ')
        if data[0].startswith('[-]') or data[0].startswith('[!]'):
            print (' '.join(data))
            return
        print(config.pos + 'Done, writing file...')
        name = basename(' '.join(data[:-1]))
        contents = b64decode(data[-1])
        with open(name, 'wb') as f:
            f.write(contents)
        print(config.pos + 'Downloaded file : ' + name)
    except (TypeError, KeyError):
        print(data)
    except Exception as e:
        print(config.neg + 'Error while downloading file : ' + str(e))
        logging.warning("Dumping stack trace and exiting...", exc_info=True)

