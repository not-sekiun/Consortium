import library.modules.config as config
from base64 import b64encode

config.main()


def main(option):
    if option == 'encode':
        try:
            imported_modules = ['from base64 import b64decode']
            with open('payload.py', 'r') as f:
                data = f.read().replace(';', '\n')
            source = data.split('\n')
            for i in source:
                if 'import' in i and i != 'from base64 import b64decode':
                    imported_modules.append(i)
            encoded_soure = b64encode(('\n'.join(source)).encode()).decode()
            obfuscated = ';'.join(imported_modules) + ';exec(b64decode("' + encoded_soure + '").decode())'
            with open('payload.py', 'w') as f:
                f.write(obfuscated)
                print('   ' + config.inf + 'Encoded scout and overwrote raw file with Base64 encoded file contents')
        except SyntaxError:
            print('   ' + config.neg + 'Could not encode scout')
    elif option == 'info':
        print('\nName             : Basic Base 64 Encoder' \
              '\nRequired Modules : base64' \
              '\nDescription      : Uses the standard Base64 algorithm and alphabet to obfuscate the scout source\n')
