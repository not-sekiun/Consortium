import library.modules.config as config

config.main()

windows_modules = []
linux_modules = []


def main():
    try:
        import sys
        import time
        import colorama
        colorama.init()
        print (config.inf + 'Starting...')
        if sys.version_info[0] == 2:
            print config.pos + 'Python Version 2 - OK'
            import platform
            import library.modules.keygen as keygen
            print config.pos + 'All local files imported - OK'
            if platform.uname()[0] == 'Windows':
                print config.pos + 'OS Windows - OK'
                for i in windows_modules:
                    exec ('import ' + i)
                    print config.pos + 'Successfully imported : ' + i + ' - OK'
                print config.pos + 'Third party imports - OK'
                keygen.main('system_initiated')
            elif platform.uname()[0] == 'Linux':
                print config.pos + 'OS Linux - OK'
                for i in linux_modules:
                    exec ('import ' + i)
                    print config.pos + 'Successfully imported : ' + i + ' - OK'
                keygen.main('system_initiated')
            else:
                print config.neg + 'OS ' + platform.uname()[0] + ' - Error, Not Supported'
                return False
        else:
            print (config.neg + 'Python Version 3 - Error, Run in Python 2')
            return False
        return True
    except ImportError as e:
        print '[-]Could not import : ' + str(e) + ' - Error, missing packages or packages not installed'
        return False
    except Exception as e:
        print config.war + 'Unexpected error when bootstrapping : ' + str(e)
