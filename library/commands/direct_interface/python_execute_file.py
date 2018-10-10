import library.modules.send_and_recv as send_and_recv
import os


def main(data, scout_id):
    file_path = data.split(' ', 1)[1]
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            data = f.read()
        print '[+]Read in data from script file : ' + file_path
        print '[*]Sending file data to scout'
        print '[*]Attempting to run on scout...'
        print send_and_recv.main('exec_py ' + data, scout_id)
    else:
        print '[-]Invalid file path supplied'
