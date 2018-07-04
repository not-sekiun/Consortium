import os

def main():
    try:
        print '[*]Opening python interpreter on local system'
        if os.name == 'nt':
            os.system('py')
        else:
            os.system('python')
    except KeyboardInterrupt:
        pass
    print '[*]Exiting...'