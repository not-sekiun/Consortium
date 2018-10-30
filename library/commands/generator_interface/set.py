import library.modules.config as config

config.main()

def main(command):
    try:
        config.scout_values[command.split(' ')[1]][0] = command.split(' ', 2)[2]
        print config.pos + 'Set "' + command.split(' ')[1] + '" to "' + command.split(' ', 2)[2] + '"'
        if config.scout_values['Windows'][0] == 'True':
            config.generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92mGenerator\033[92m\x1b[1m\x1b[37m\x1b[1m\x1b[37m@\x1b[0m\033[92mWindows\033[92m\x1b[1m\x1b[37m) > \x1b[0m'
        else:
            config.generator_prompt = '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[92mGenerator\033[92m\x1b[1m\x1b[37m\x1b[1m\x1b[37m@\x1b[0m\033[92mLinux\033[92m\x1b[1m\x1b[37m) > \x1b[0m'
    except (IndexError, KeyError):
        print config.neg + 'Please specify a valid option and value'