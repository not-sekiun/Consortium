import os
import time
import moved_modules.randomized_output as randomized_output


def set_creds():
    os.chdir('../')
    if not os.path.isfile('persistent_creds.txt'):
        server_key = raw_input('[>]Set a default listener key [Enter to generate random key] : ')
        if not server_key:
            server_key = randomized_output.rand_string(50)
        print '[+]Set listener key to : ' + server_key
        scout_identifier = raw_input('[>]Set a default scout key [Enter to generate random key] : ')
        if not scout_identifier:
            scout_identifier = randomized_output.rand_string(50)
        print '[+]Set scout key to : ' + scout_identifier
        f = open('persistent_creds.txt','w')
        f.write(server_key + '\n' + scout_identifier + '\n' + randomized_output.rand_string(50))
        f.close()
        print '[+]Set credentials'
    else:
        f = open('persistent_creds.txt','r')
        test_empty_string = f.read().split('\n')
        if len(test_empty_string) < 3:
            print '[-]persistent_cred.txt has been tampered with, resetting creds...'
            server_key = raw_input('[>]Set a default listener key [Enter to generate random key] : ')
            if not server_key:
                server_key = randomized_output.rand_string(50)
            print '[+]Set listener key to : ' + server_key
            scout_identifier = raw_input('[>]Set a default scout key [Enter to generate random key] : ')
            if not scout_identifier:
                scout_identifier = randomized_output.rand_string(50)
            print '[+]Set scout key to : ' + scout_identifier
            f = open('persistent_creds.txt', 'w')
            f.write(server_key + '\n' + scout_identifier + '\n' + randomized_output.rand_string(50))
            f.close()
            print '[+]Set credentials'
        else:
            print '[+]Credentials already set'

set_creds()
