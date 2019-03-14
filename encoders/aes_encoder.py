import library.modules.config as config
from base64 import b64encode

config.main()


def main(option, filepath=None):
    if not filepath:
        filepath = config.scout_values['Path'][0]
    if option == 'encode':
        try:
            imported_modules = ['from Crypto.Cipher import AES']
            with open(filepath, 'r') as f:
                data = f.read().replace(';', '\n')
            source = data.split('\n')
            for i in source:
                if 'import' in i and i != 'from Crypto.Cipher import AES':
                    imported_modules.append(i)
            obfuscated = ';'.join(imported_modules) + ';exec(b64decode("' + b64encode('\n'.join(source)) + '"))'
            with open(filepath, 'w') as f:
                f.write(obfuscated)
                print '   ' + config.inf + 'Encoded scout and overwrote raw file with AES encoded file contents'
        except SyntaxError:
            print '   ' + config.neg + 'Could not encode scout'
    elif option == 'info':
        print '\nName             : AES Encoder' \
              '\nRequired Modules : pycryptodome' \
              '\nDescription      : Uses the standard AES algorithm to symmetrically encrypt the scout source\n'
