import library.modules.send_and_recv as send_and_recv
import os
import library.modules.config as config

config.main()


def main(data, scout_id):
    file_path = data.split(' ', 1)[1]
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            data = f.read()
        print(config.pos + 'Read in data from script file : ' + file_path)
        print(config.inf + 'Sending file data to scout')
        print(config.inf + 'Attempting to run on scout...')
        print(send_and_recv.main('exec_py ' + data, scout_id))
    else:
        print(config.neg + 'Invalid file path supplied')
