import library.modules.recv_all as recv_all
from base64 import b64encode
from ntpath import basename
import library.modules.config as config
import library.modules.send_all as send_all

config.main()


def main(sock, filepath):
    try:
        filepath = filepath.split(' ', 1)[1]
        print(config.inf + 'Reading file...')
        with open(filepath, 'rb') as f:
            data = f.read()
        print(config.inf + 'Sending file data to scout...')
        send_all.main(sock, 'upload ' + basename(filepath) + ' ' + b64encode(data).decode())
        response = recv_all.main(sock)
        print(response)
    except IOError:
        print(config.neg + 'File does not exist, cannot upload')
    except IndexError:
        print(config.neg + 'Please supply valid arguments for the command you are running')
    except Exception as e:
        print(config.neg + 'Error while uploading file : ' + str(e))
