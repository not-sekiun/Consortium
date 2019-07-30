import library.modules.config as config
from cryptography.fernet import Fernet

config.main()


def main(option, filepath=None):
    if not filepath:
        filepath = config.scout_values['Path'][0]
    if option == 'encode':
        try:
            imported_modules = ['from cryptography.fernet import Fernet']
            with open(filepath, 'r') as f:
                data = f.read().replace(';', '\n')
            source = data.split('\n')
            for i in source:
                if 'import' in i and i != 'from cryptography.fernet import Fernet':
                    imported_modules.append(i)
            key = Fernet.generate_key()
            print '   ' + config.inf + 'Fernet generated cipher key for AES symmetrical encryption : ' + key
            cipher_suite = Fernet(key)
            encoded_source = cipher_suite.encrypt('\n'.join(source))
            obfuscated = ';'.join(
                imported_modules) + ';cipher_suite = Fernet("' + key + '");exec(cipher_suite.decrypt("' + encoded_source + '"))'
            with open(filepath, 'w') as f:
                f.write(obfuscated)
                print '   ' + config.inf + 'Encoded scout and overwrote raw file with AES encrypted file contents using Fernet'
        except SyntaxError:
            print '   ' + config.neg + 'Could not encode scout'
    elif option == 'info':
        print '\nName             : AES Encoder' \
              '\nRequired Modules : cryptography (Fernet function from cryptography module)' \
              '\nDescription      : Uses Fernet to AES encrypt the scout\n'
