import os

def main():
    try:
        print '[*]Opening python interpreter on local system'
        os.system('python')
    except KeyboardInterrupt:
        pass
    print '[*]Exiting...'