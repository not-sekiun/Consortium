import os
import library.modules.return_random_string as return_random_string
import library.modules.config as config

config.main()

def main(condition):
    if condition == 'system_initiated':
        dir = os.listdir(os.getcwd())
        if 'PyIris.cred' in dir:
            print '[+]PyIris.cred key file located - OK'
            pass
        else:
            print '[-]PyIris.cred key file not found/generated - ERROR, AUTO-GENERATING KEY'
            prompt = raw_input('[>]Listener key [Enter to generate a random 50 length key] : ')
            if not prompt:
                prompt = return_random_string.main(50)
            f = open('PyIris.cred','w')
            f.write(prompt)
            f.close()
            print '[+]Generated PyIris.cred key file with key as : ' + prompt
    elif condition == 'user_initiated':
        continue_on = raw_input('[!]This will overwrite existing key, continue? [y|n] : ')
        if continue_on == 'y':
            prompt = raw_input('[>]Listener key [Enter to generate a random 50 length key] : ')
            if not prompt:
                prompt = return_random_string.main(50)
            f = open('PyIris.cred', 'w')
            f.write(prompt)
            f.close()
            print '[+]Generated PyIris.cred key file with key as : ' + prompt
            config.key = prompt