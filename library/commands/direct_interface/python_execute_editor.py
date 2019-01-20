import time
import library.modules.config as config

config.main()


def main():
    print config.war + 'You are currently in the python executor scripter, script a chain of python instructions to run, enter for a newline, CTRL-C to finish ' \
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
            print
            '\n' + config.pos + 'Done'
            return command
    except KeyboardInterrupt:
        print
        '\n' + config.pos + 'Done'
        return command
