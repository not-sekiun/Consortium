from random import choice


def display_banner():
    version = '0.3.0'
    sample_space = [(
                    '\x1b[1m\x1b[37m\n                          ---===[ \x1b[0m' + '\x1b[1m\x1b[31mVersion : ' + version + '\x1b[0m' + '\x1b[1m\x1b[37m ]===---\n\n\x1b[0m' +
                    """\x1b[1m\x1b[36m                     dBBBBBb  dBp   dBp dBP dBBBBBb    dBP .dBBBBP
                          dB'  dBp dBP          dBP        BP     
                      dBBBP'     dBP  dBp  dBBBBK'   dBP   `BBBBb 
                     dBP        dBP  dBp  dBP   BB  dBP       dBP 
                    dBP        dBP  dBp  dBP   dB' dBP   dBBBBP'\n\x1b[0m""" +
                    '\x1b[1m\x1b[31m\n                        Full Fledged Reverse Shell Toolkit    \n\x1b[0m' +
                    '\x1b[1m\x1b[37m\n               Developer : \x1b[0m' + '\x1b[1m\x1b[31mAngus, at https://www.github.com/angus-y\x1b[0m\n' +
                    '\x1b[1m\x1b[37m               Name      : \x1b[0m' + '\x1b[1m\x1b[31mPython-Iris(PyIris)\n\n\x1b[0m'),
                    (
                    '\x1b[1m\x1b[37m\n                          ---===[ \x1b[0m' + '\x1b[1m\x1b[31mVersion : ' + version + '\x1b[0m' + '\x1b[1m\x1b[37m ]===---\n\n\x1b[0m' +
                    '''                          __________________________
                              |___o___|
                                 | |
                             ____|_|____________
                            |__________________/_
                            |      CCTV     /____|
                            |______________/\n''' +
                    '\x1b[1m\x1b[31m\n                        PyIris, the virtual spy camera    \n\x1b[0m' +
                    '\x1b[1m\x1b[37m\n               Developer : \x1b[0m' + '\x1b[1m\x1b[31mAngus, at https://www.github.com/angus-y\x1b[0m\n' +
                    '\x1b[1m\x1b[37m               Name      : \x1b[0m' + '\x1b[1m\x1b[31mPython-Iris(PyIris)\n\n\x1b[0m')]
    print choice(sample_space)
