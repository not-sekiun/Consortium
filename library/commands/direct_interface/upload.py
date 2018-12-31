import library.modules.recv_all as recv_all
import time
import pickle
from ntpath import basename
import library.modules.config as config

config.main()


def main(sock, filepath):
    try:
        filepath = filepath.split(' ', 1)[1]
        print config.inf + 'Reading file...'
        print config.inf + 'Initiating file upload with scout...'
        sock.sendall('upload')
        time.sleep(3)
        with open(filepath, 'rb') as f:
            data = f.read()
        pickle_data = pickle.dumps([basename(filepath), data])
        print config.pos + 'Done, uploading file...'
        sock.sendall(pickle_data)
        response = recv_all.main(sock)
        print response
    except IOError:
        print config.neg + 'File does not exist, cannot upload'
    except IndexError:
        print config.neg + 'Please supply valid arguments for the command you are running'
    except Exception as e:
        print config.neg + 'Error while uploading file : ' + str(e)
