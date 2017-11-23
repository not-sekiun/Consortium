from termcolor import colored

def display_banner():
	print colored('\n                          ---===[ ','white',attrs=['bold'])+colored('Version : 0.1.0','red',attrs=['bold'])+colored(' ]===---\n','white',attrs=['bold'])
	
	print colored("""                     dBBBBBb  dBp   dBp dBP dBBBBBb    dBP .dBBBBP
                          dB'  dBp dBP          dBP        BP     
                      dBBBP'     dBP  dBp  dBBBBK'   dBP   `BBBBb 
                     dBP        dBP  dBp  dBP   BB  dBP       dBP 
                    dBP        dBP  dBp  dBP   dB' dBP   dBBBBP'""",'cyan',attrs=['bold'])
	print colored('\n                        Full Fledged Reverse Shell Toolkit    ','red',attrs=['bold'])
	print colored('\n               Developer : ','white',attrs=['bold'])+colored('Angus, at https://www.github.com/angus-y','red',attrs=['bold'])
	print colored('               Name      : ','white',attrs=['bold'])+colored('Python-Iris(PyIris)\n','red',attrs=['bold'])