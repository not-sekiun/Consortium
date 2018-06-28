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
def mainGUI(prompt):
    try:
        try:
            prompt = prompt.split(' ',1)[1]
        except IndexError:
            return '[-]Please supply an argument as the command to execute locally'
        if prompt[:3] == 'cd ':
            try:
                os.chdir(prompt[3:])
                return '[+]Changed to directory : ' + prompt[3:] + '\n'
            except (WindowsError, OSError):
                return '[-]Could not change to directory : ' + prompt[3:] + '\n'
        else:
            result = subprocess.Popen(prompt, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            result = result.stdout.read() + result.stderr.read()
            return result
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '[*]Cancelled local command execution'
    except KeyboardInterrupt:
        print '[*]Cancelled local command execution'