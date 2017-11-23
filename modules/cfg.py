from termcolor import colored

def global_variables():
	scouts_id=0
	listeners_id=0
	prompt_default=colored('PyIris > ','white',attrs=['bold'])
	prompt_listener=colored('PyIris (','white',attrs=['bold'])+colored('Listener','blue',attrs=['bold'])+colored(') > ','white',attrs=['bold'])
	prompt_scouts=colored('PyIris (','white',attrs=['bold'])+colored('Scouts','blue',attrs=['bold'])+colored(') > ','white',attrs=['bold'])
	err=colored('[-]','red',attrs=['bold'])
	note=colored('[*]','blue',attrs=['bold'])
	pos=colored('[+]','green',attrs=['bold'])
	shutdown=colored('[!]User requested shutdown...','red',attrs=['bold'])
	help_root='''\nPyIris Help Menu
===================

   Global Commands :
      banner                            Display a banner
      help                              Show the help menu
      quit                              Quit the console
      clear                             Clear the screen

   PyIris Commands :
      global_add <wh_list/bl_list> <IP> Add IP to global blacklist/whitelist
      global_rm <wh_list/bl_list> <IP>  Remove IP from global blacklist/whitelist
      listeners                         Change to listeners menu
      scouts                            Change to scouts menu
      show                              Show IP whitelist and blacklist
      wipe                              Reset global blacklist and whitelist\n'''
	help_listener='''\nListener Help Menu
==================
   
   Global Commands :
      banner                            Display a banner
      help                              Show the help menu
      quit                              Quit the console
      clear                             Clear the screen

   Listener Commands :
      back                              Move back a mode
      kill <ID>                         Kill a listener by it's ID
      kill_all                          Kill all listeners
      show                              Show all active listeners
      start <port number>               Start a listener\n'''
	help_scouts='''\nScouts Help Menu
================
   
   Global Commands :
      banner                            Display a banner
      help                              Show the help menu
      quit                              Quit the console
      clear                             Clear the screen

   Scout Commands :
      back                              Move back a mode
      bridge                            Bridge/connect to a scout to start interacting with it
      kill <ID>                         Kill a scout by its ID
      kill_all                          Kill all connected scouts
      show                              Show all online scouts\n'''
	blacklisted_ip=[]
	whitelisted_ip=[]
	db_scouts=[]
	db_listeners=[]
	key='LdtwGvWUNeuRqrxCjpMyFEhnOPsISzBbTfQKVAZkDiomlJHgcX'
	End='vfyNAiIeoLbExRYCMWzJtXqcDFZlrapVTKgBmUshSjPkGQHdnu'
	globals().update(locals())