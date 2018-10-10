import library.modules.recv_all as recv_all
import pickle
from ntpath import basename


def main(sock):
    try:
        print '[*]Receiving data...'
        pickle_data = recv_all.main(sock)
        data = pickle.loads(pickle_data)
        print '[+]Done, writing file...'
        name = basename(data[0])
        contents = data[1]
        f = open(name, 'wb')
        f.write(contents)
        f.close()
        print '[+]Downloaded file : ' + name
    except (TypeError, KeyError):
        print pickle_data
    except Exception as e:
        print '[-]Error while downloading file : ' + str(e)
