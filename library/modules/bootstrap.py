windows_modules = []
linux_modules = []

def main():
    try:
        import sys
        import time
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
        else:
            print ('[-]Python Version 3 - Error, Run in Python 2')
            return False
        return True
    except ImportError as e:
        print '[-]Could not import : ' + str(e) + ' - Error, missing packages or packages not installed'
        return False
    except Exception as e:
        print '[!]Unexpected error when bootstrapping : ' + str(e)
def mainGUI(app):
    try:
        import sys
        import time
        app.addLabel('[*]Starting...')
        if sys.version_info[0] == 2:
            app.addLabel('[+]Python Version 2 - OK')
            import platform
            import library.modules.keygen as keygen
            app.addLabel('[+]All local files imported - OK')
            if platform.uname()[0] == 'Windows':
                app.addLabel('[+]OS Windows - OK')
                for i in windows_modules:
                    exec('import ' + i)
                    app.addLabel('[+]Successfully imported : ' + i + ' - OK')
                    app.addLabel('[+]Third party imports - OK')
                keygen.main('system_initiated')
            elif platform.uname()[0] == 'Linux':
                app.addLabel('[+]OS Linux - OK')
                for i in linux_modules:
                    exec('import ' + i)
                    app.addLabel('[+]Successfully imported : ' + i + ' - OK')
                keygen.main('system_initiated')
            else:
                app.addLabel('os_error','[-]OS ' + platform.uname()[0] + ' - Error, Not Supported')
                app.setLabelBg('os_error','red')
                return False
        else:
            app.addLabel('python_ver_error','[-]Python Version 3 - Error, Run in Python 2')
            app.setLabelBg('python_ver_error','red')
            return False
        return True
    except ImportError as e:
        app.addLabel('import_error','[-]Could not import : ' + str(e) + ' - Error, missing packages or packages not installed')
        app.setLabelBg('import_error', 'red')
        return False
    except Exception as e:
        app.addLabel('bootstrap_error','[!]Unexpected error when bootstrapping : ' + str(e))
        app.setLabelBg('bootstrap_error','red')
        return False