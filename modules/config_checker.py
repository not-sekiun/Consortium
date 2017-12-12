import cfg

cfg.global_variables()

def exit_program():
    print '[*]If there are any issues contact me by posting an issue on github or by emailing me at 1010angusx@gmail.com'
    print '[*]EXITING...'
    exit()

def test():
    try:
        f = open('persistent_data.txt','r')
        data = f.read()
        data = data.split('\n')
        if data[0] == 'Passed':
            version = data[2]
            if version == cfg.toolkit_version:
                return
            else:
                print '[*]New version detected, re-running config checker'
                raise SyntaxError
        else:
            print '[-]persistent_data.txt seems to have been tampered with, re-running config checker'
            raise SyntaxError
    except:
        try:
            default_modules = ['sys','os','socket','time','platform','random','datetime','pickle','subprocess','getpass']
            external_win_modules = ['colorama','comtypes','docx','mss','pyaudio','pyautogui','pycaw','pyHook','win32api']
            external_lin_modules = ['colorama','pyautogui','docx']

            for i in default_modules:
                try:
                    exec('import '+i)
                    print '[*]Imported default python module : '+i
                except ImportError:
                    print ('\n[-]Failed when importing default module: ' + i)
                    print ('[*]Note : Unable to Import default python module : '+i+'. Try reinstalling your system version of python 2.X')
                    exit_program()
            print ('[+]Passed : Imported default python modules, no anomalies with your python install')

            if platform.uname()[0] == 'Windows':
                print '[*]Detected : ' + '-'.join(platform.uname())
                print '[+]Passed : Major Version Windows detected'
            elif platform.uname()[0] == 'Linux':
                print '[*]Detected : ' + '-'.join(platform.uname())
                print '[+]Passed : Major Version Linux detected'
            else:
                print '[-]Detected : ' + '-'.join(platform.uname())
                print '\n[-]Failed upon detecting an OS that is neither Windows or Linux'
                print '[*]Note : This toolkit was developed and made for linux/windows please use those respective operating systems'
                exit_program()

            if platform.uname()[0] == 'Windows':
                for i in external_win_modules:
                    try:
                        exec('import '+i)
                        print '[*]Imported third party module : '+i
                    except ImportError:
                        print '\n[-]Failed when importing third party lib : '+i
                        print '[*]Note : If you have not, run pip C:\python27\scripts\pip install -r windows_requirements.txt in cmd.'
                        print 'Your path may not have to have python27 but python 2.7 is the most preferred version of python to use'
                        exit_program()
                print '[+]Passed : Third party Windows modules installed'
            elif platform.uname()[0] == 'Linux':
                for i in external_lin_modules:
                    try:
                        exec('import '+i)
                        print '[*]Imported third party module : '+i
                    except ImportError:
                        print '\n[-]Failed when importing third party lib : '+i
                        print '[*]Note : If you have not done so yet run the following as root : \n[1]pip install python3-xlib\n[2]apt-get install scrot\n[3]apt-get install python3-tk\n[4]apt-get install python3-dev\n[5]apt-get install portaudio19-dev\n[6]apt-get install python-alsaaudio\n[7]apt-get install python-wnck[8]pip2 install -r linux_requirements.txt'
                        exit_program()
                print '[+]Passed : Third party linux modules installed'

            subfolders = [name for name in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(), name))]
            if 'modules' in subfolders:
                print '[*]Located modules folder'
                if 'payloads' in subfolders:
                    print '[*]Located payloads folder'
                else:
                    print '\n[-]Failed, cannot find subfolder payloads'
                    print '[*]Note : Do not modify the subfolders please reinstall PyIris from github.'
                    exit_program()
            else:
                print '\n[-]Failed, cannot find subfolder modules'
                print '[*]Note : Do not modify the subfolders please reinstall PyIris from github.'
                exit_program()
            print '[+]Passed : Default directory subfolders detected'

            end_test = raw_input('[*]Passed all requirements, thanks for installing [Enter to continue]')
            f=open('persistent_data.txt','w')
            f.write('Passed'+'\n'+time.strftime('%d/%m/%Y')+'\n'+cfg.toolkit_version)
            f.close()
        except KeyboardInterrupt:
            print '[-]Config check interrupted'
            exit_program()
        except EOFError:
            print '[-]Config check interrupted'
            try:
                exit_program()
            except KeyboardInterrupt:
                exit_program()