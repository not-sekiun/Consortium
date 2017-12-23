import pickle
import cfg
from random import choice

cfg.global_variables()

def banner():
    version = cfg.framework_version
    try:
        f = open('persistent_data.pkl','rb')
        last_updated = pickle.loads(f.read())['time_downloaded']
        f.close()
    except:
        last_updated = '?????'
    sample_space = [(
                    '\x1b[1m\x1b[37m\n                          ---===[ \x1b[0m' + '\x1b[1m\x1b[31mVersion : ' + version + '\x1b[0m' + '\x1b[1m\x1b[37m ]===---\n\n\x1b[0m' +
                    """\x1b[1m\x1b[36m                     dBBBBBb  dBp   dBp dBP dBBBBBb    dBP .dBBBBP
                          dB'  dBp dBP          dBP        BP     
                      dBBBP'     dBP  dBp  dBBBBK'   dBP   `BBBBb 
                     dBP        dBP  dBp  dBP   BB  dBP       dBP 
                    dBP        dBP  dBp  dBP   dB' dBP   dBBBBP'\n\x1b[0m""" +
                    '\x1b[1m\x1b[31m\n                        Full Fledged Remote access Framework\n\x1b[0m' +
                    '\x1b[1m\x1b[37m\n               Developer    : \x1b[0m' + '\x1b[1m\x1b[31mAngus, at https://www.github.com/angus-y\x1b[0m\n' +
                    '\x1b[1m\x1b[37m               Name         : \x1b[0m' + '\x1b[1m\x1b[31mPython-Iris(PyIris)\n\x1b[0m'+
                    '\x1b[1m\x1b[37m               Last updated : \x1b[0m' + '\x1b[1m\x1b[31m'+last_updated+'\n\n\x1b[0m'
                    ),
                    (
                    '\x1b[1m\x1b[37m\n                          ---===[ \x1b[0m' + '\x1b[1m\x1b[31mVersion : ' + version + '\x1b[0m' + '\x1b[1m\x1b[37m ]===---\n\n\x1b[0m' +
                    '''                          __________________________
                              |___o___|
                                 | |
                             ____|_|____________
                            |__________________/_
                            |      CCTV     /____|
                            |______________/\n''' +
                    '\x1b[1m\x1b[31m\n                             AV Evasive remote access\n\x1b[0m' +
                    '\x1b[1m\x1b[37m\n               Developer    : \x1b[0m' + '\x1b[1m\x1b[31mAngus, at https://www.github.com/angus-y\x1b[0m\n' +
                    '\x1b[1m\x1b[37m               Name         : \x1b[0m' + '\x1b[1m\x1b[31mPython-Iris(PyIris)\n\x1b[0m' +
                    '\x1b[1m\x1b[37m               Last updated : \x1b[0m' + '\x1b[1m\x1b[31m' + last_updated + '\n\n\x1b[0m'
                    ),
                    ('\x1b[1m\x1b[37m\n                          ---===[ \x1b[0m' + '\x1b[1m\x1b[31mVersion : ' + version + '\x1b[0m' + '\x1b[1m\x1b[37m ]===---\n\n\x1b[0m' +
                     '''                                   \x1b[1m\x1b[31m_____________
                                  /  ____\x1b[1m\x1b[37mo\x1b[0m\x1b[1m\x1b[31m____  \\
                                  | |\x1b[0m\x1b[1m\x1b[37mPYIRIS >\x1b[0m \x1b[1m\x1b[31m| |
                                  | |_________| |
                                  \\_____________/
                                  ______/ \_______
                                 /_/_/_/_/_/_/_/_/|\x1b[0m
                           _____\x1b[1m\x1b[31m/_/_/_/_/_/_/_/_//\x1b[0m_____
                          |                            |
                    \x1b[1m\x1b[31m______\x1b[0m\x1b[0m\x1b[1m\x1b[37mV\x1b[0m\x1b[1m\x1b[31m______\x1b[0m                \x1b[1m\x1b[31m______\x1b[0mV\x1b[1m\x1b[31m______\x1b[0m
                   \x1b[1m\x1b[31m/  ____\x1b[0m\x1b[0m\x1b[1m\x1b[37mo\x1b[0m\x1b[1m\x1b[31m____  \\\x1b[0m              \x1b[1m\x1b[31m/  ____\x1b[1m\x1b[37mo\x1b[0m\x1b[1m\x1b[31m____  \\\x1b[0m
                   \x1b[1m\x1b[31m| |\x1b[0m\x1b[1m\x1b[37mSCOUT   \x1b[0m \x1b[1m\x1b[31m| |\x1b[0m              \x1b[1m\x1b[31m| |\x1b[0m\x1b[1m\x1b[37mSCOUT   \x1b[0m \x1b[1m\x1b[31m| |\x1b[0m
                   \x1b[1m\x1b[31m| |_________| |\x1b[0m              \x1b[1m\x1b[31m| |_________| |\x1b[0m
                   \x1b[1m\x1b[31m\\_____________/\x1b[0m              \x1b[1m\x1b[31m\\_____________/\x1b[0m
                       \x1b[1m\x1b[31m__/ \__\x1b[0m                      \x1b[1m\x1b[31m__/ \__\x1b[0m'''
                     '\x1b[1m\x1b[31m\n\n                  Centralised command and control infrastructure\n\x1b[0m' +
                     '\x1b[1m\x1b[37m\n               Developer    : \x1b[0m' + '\x1b[1m\x1b[31mAngus, at https://www.github.com/angus-y\x1b[0m\n' +
                    '\x1b[1m\x1b[37m               Name         : \x1b[0m' + '\x1b[1m\x1b[31mPython-Iris(PyIris)\n\x1b[0m'+
                    '\x1b[1m\x1b[37m               Last updated : \x1b[0m' + '\x1b[1m\x1b[31m'+last_updated+'\n\n\x1b[0m'
                     )]
    print choice(sample_space)
