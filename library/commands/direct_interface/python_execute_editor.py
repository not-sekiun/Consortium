import time


def main():
    print '[!]You are currently in the python executor scripter, script a chain of python instructions to run, enter for a newline ' \
          '\n(only works if python execute component is loaded)'
    try:
        command = ''
        while True:
            line = '\n' + raw_input('Python Executor Scripter >>> ')
            command += line
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '\n[+]Done'
            return command
    except KeyboardInterrupt:
        print '\n[+]Done'
        return command
