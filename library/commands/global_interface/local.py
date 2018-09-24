import os
import subprocess
import time

def main(prompt):
    try:
        try:
            prompt = prompt.split(' ',1)[1]
        except IndexError:
            print '[-]Please supply an argument as the command to execute locally'
            return
        print '\n[*]Executing locally...\n'
        if prompt[:3] == 'cd ':
            try:
                os.chdir(prompt[3:])
                print '[+]Changed to directory : ' + prompt[3:] + '\n'
            except (WindowsError, OSError):
                print '[-]Could not change to directory : ' + prompt[3:] + '\n'
        else:
            result = subprocess.Popen(prompt, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            result = result.stdout.read() + result.stderr.read()
            print result
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '[*]Cancelled local command execution'
    except KeyboardInterrupt:
        print '[*]Cancelled local command execution'