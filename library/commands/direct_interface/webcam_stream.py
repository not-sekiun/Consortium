import library.modules.config as config
import library.modules.recv_all as recv_all
import library.modules.send_all as send_all
import pickle
import cv2

config.main()


def main(sock):
    print (config.inf + 'Streaming clients webcam, press "q" in the live stream window to exit')
    while True:
        data = recv_all.main(sock)
        if type(data) == str:
            print (data)
            return
        else:
            frame = pickle.loads(data)
            cv2.imshow('Live stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                send_all.main(sock, "1")
                cv2.destroyAllWindows()
                print (recv_all.main(sock))
                break
            send_all.main(sock, "0")
