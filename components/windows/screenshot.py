import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyscreenshot as ImageGrab')
        config.import_statements.append('import pickle')
        config.functions.append('''
def screenshot():
    im = ImageGrab.grab()
    bytes = pickle.dumps(im)
''')
