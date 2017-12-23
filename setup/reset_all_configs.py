import os

try:
    os.chdir('../')
    os.remove('persistent_creds.txt')
    print '[+]Removed persistent credentials'
    os.remove('persistent_data.pkl')
    print '[+]Removed persistent data'
    print '[+]Finished resetting all configs'
except (WindowsError,OSError):
    print '[+]Finished resetting all configs'
except Exception as e:
    print '[-]Error while resetting all configurations : ' + str(e)
