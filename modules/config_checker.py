import platform
import pickle
import time
import cfg

cfg.global_variables()

def exit_program():
    print '[*]If there are any issues contact me by posting an issue on github or by emailing me at 1010angusx@gmail.com'
    print '[*]EXITING...'
    exit()

def test():
    try:
        exec('import pickle')
        f = open('persistent_data.pkl','rb')
        data = pickle.loads(f.read())
        f.close()
        if data['test_status'] == 'Passed':
            if data['current_version'] == cfg.framework_version:
                return
            else:
                print '[*]New version detected, re-running config checker'
                raise SyntaxError
        else:
            print '[-]persistent_data file seems to have been tampered with, re-running config checker'
            raise SyntaxError
    except:
        try:
            external_win_modules = ['colorama','comtypes','docx','mss','pyaudio','pyautogui','pycaw','pyHook','win32api','wave','cv2']
            external_lin_modules = ['colorama','pyautogui','docx','mss','pyaudio','wave','pyxhook','alsaaudio','clipboard','cv2']

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
                        print '[*]Note : If you have not, run C:\python27\scripts\pip install -r windows_requirements.txt in cmd.'
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
                        print 'Note : please pip install the required modules from either lin_requirements.txt or win_requirements.txt.'
                        print 'P.S  : run linux_set_pip.py before pip installing'
                        exit_program()
                print '[+]Passed : Third party linux modules installed'
            end_test = raw_input('[*]Passed all requirements, thanks for installing [Enter to continue]')
            config_dict = {'test_status':'Passed','time_downloaded':time.strftime('%d/%m/%Y'),'current_version':cfg.framework_version}
            f=open('persistent_data.pkl','wb')
            f.write(pickle.dumps(config_dict))
            f.close()
        except KeyboardInterrupt:
            print '[!]User requested shutdown...'
            exit_program()
        except EOFError:
            print '[!]User requested shutdown...'
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                exit_program()