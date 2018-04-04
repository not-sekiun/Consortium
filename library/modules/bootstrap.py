windows_modules = []
linux_modules = []

def main():
    try:
        import sys
        print ('[*]Starting...')
        if sys.version_info[0] == 2:
            print '[+]Python Version 2 - OK'
            import platform
            import library.modules.keygen as keygen
            print '[+]All local files imported - OK'
            if platform.uname()[0] == 'Windows':
                print '[+]OS Windows - OK'
                for i in windows_modules:
                    exec('import ' + i)
                    print '[+]Successfully imported : ' + i + ' - OK'
                print '[+]Third party imports - OK'
                keygen.main('system_initiated')
            elif platform.uname()[0] == 'Linux':
                print '[+]OS Linux - OK'
                for i in linux_modules:
                    exec('import ' + i)
                    print '[+]Successfully imported : ' + i + ' - OK'
                keygen.main('system_initiated')
            else:
                print '[-]OS ' + platform.uname()[0] + ' - Error, Not Supported'
                return False
            print '[+]Started Successfully'
        else:
            print ('[-]Python Version 3 - Error, Run in Python 2')
            return False
        return True
    except ImportError as e:
        print '[-]Could not import : ' + str(e) + ' - Error, missing packages or packages not installed'
        return False
    #except Exception as e:
    #    print '[!]Unexpected error when bootstrapping : ' + str(e)