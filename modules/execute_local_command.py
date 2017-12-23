import subprocess
import os
import cfg

cfg.global_variables()

def execute(command):
    print '\n' + cfg.note + 'Executing locally...\n'
    if command[:3] == 'cd ':
        try:
            os.chdir(command[3:])
            print cfg.pos + "Changed to directory : " + command[3:] + '\n'
        except (WindowsError, OSError):
            print cfg.err + 'Could not change to directory : ' + command[3:] + '\n'
    else:
        result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE)
        result = result.stdout.read() + result.stderr.read()
        print result