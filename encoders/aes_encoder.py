import library.modules.config as config
import library.modules.return_random_string as return_random_string
from base64 import b64encode

config.main()
sym_key = None

def aes_encode():
    global sym_key




def main(option, filepath=None):
    global sym_key
    sym_key = return_random_string.main(32)
    if not filepath:
        filepath = config.scout_values['Path'][0]
    if option == 'encode':
        try:
            imported_modules = ['from Crypto.Cipher import AES']
            with open(filepath, 'r') as f:
                data = f.read().replace(';', '\n')
            source = data.split('\n')
            for i in source:
                if 'import' in i and i != 'from base64 import b64decode':
                    imported_modules.append(i)
            obfuscated = ';'.join(imported_modules) + ';exec(b64decode("' + b64encode('\n'.join(source)) + '"))'
            with open(filepath, 'w') as f:
                f.write(obfuscated)
                print '   ' + config.inf + 'Encoded scout and overwrote raw file with Base64 encoded file contents'
        except SyntaxError:
            print '   ' + config.neg + 'Could not encode scout'
    elif option == 'info':
        print '\nName             : AES Encoder' \
              '\nRequired Modules : base64' \
              '\nDescription      : Uses the standard AES algorithm encrypt the scout source with a random 56 bit key\n'
