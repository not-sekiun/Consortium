import library.modules.recv_all as recv_all
import pickle
from ntpath import basename
import library.modules.config as config

config.main()

def main(sock):
    try:
        print config.inf + 'Receiving data...'
        pickle_data = recv_all.main(sock)
        data = pickle.loads(pickle_data)
        print config.pos + 'Done, writing file...'
        name = basename(data[0])
        contents = data[1]
        with open(name, 'wb') as f:
            f.write(contents)
        print config.pos + 'Downloaded file : ' + name
    except (TypeError, KeyError):
        print pickle_data
    except Exception as e:
        print config.neg + 'Error while downloading file : ' + str(e)
