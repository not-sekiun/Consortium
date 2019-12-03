import os
import subprocess
import time
import library.modules.config as config

config.main()


def main(prompt):
    try:
        try:
            prompt = prompt.split(' ', 1)[1]
        except IndexError:
            print(config.neg + 'Please supply an argument as the command to execute locally')
            return
        print('\n' + config.inf + 'Executing locally...\n')
        if prompt[:3] == 'cd ':
            try:
                os.chdir(prompt[3:])
                print(config.pos + 'Changed to directory : ' + prompt[3:] + '\n')
            except (WindowsError, OSError):
                print(config.neg + 'Could not change to directory : ' + prompt[3:] + '\n')
        else:
            result = subprocess.Popen(prompt, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            result = result.stdout.read() + result.stderr.read()
            print(result.decode())
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print(config.inf + 'Cancelled local command execution')
    except KeyboardInterrupt:
        print(config.inf + 'Cancelled local command execution')
