import base64
import library.modules.config as config
from itertools import cycle
from library.modules import return_random_string

config.main()


def xor_encoder(plaintext, cipher):
    encrypted = []
    for (char_1, char_2) in zip(plaintext, cycle(cipher)):
        encrypted.append(chr(ord(char_1) ^ ord(char_2)))
    return "".join(encrypted)


def main(option, filepath=None):
    if not filepath:
        filepath = config.scout_values['Path'][0]
    if option == 'encode':
        try:
            imported_modules = ['from itertools import cycle', 'from base64 import b64decode']
            with open(filepath, 'r') as f:
                data = f.read().replace(';', '\n')
            source = data.split('\n')
            for i in source:
                if 'import' in i and i != 'from itertools import cycle':
                    imported_modules.append(i)
            key = return_random_string.main(50)
            print('   ' + config.inf + 'Random 50 length XOR cipher key : ' + key)
            encoded_source = base64.b64encode((xor_encoder('\n'.join(source), key)).encode()).decode()
            obfuscated = ';'.join(
                imported_modules) + ';exec("".join(chr(ord(c1)^ord(c2)) for (c1,c2) in zip(b64decode("' + encoded_source + '").decode(),cycle("' + key + '"))))'
            with open(filepath, 'w') as f:
                f.write(obfuscated)
                print('   ' + config.inf + 'Encoded scout and overwrote raw file with XOR encoded file contents')
        except SyntaxError:
            print('   ' + config.neg + 'Could not encode scout')
    elif option == 'info':
        print('\nName             : XOR Cipher Encoder' \
              '\nRequired Modules : itertools, base64' \
              '\nDescription      : Uses XOR cipher encryption to obfuscate the scout source' \
              '\nNote             : Requires base64 module to encode raw bytes as text so the scout is able to base64 decode itself into raw bytes to XOR decrypt itself\n')
