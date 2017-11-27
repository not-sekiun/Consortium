def global_variables():
    scouts_id = 0
    listeners_id = 0
    prompt_default = '\x1b[1m\x1b[37mPyIris > \x1b[0m'
    prompt_listener = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[34mListeners\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    prompt_scouts = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[34mScouts\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    err = '\x1b[1m\x1b[31m[-]\x1b[0m'
    note = '\x1b[1m\x1b[34m[*]\x1b[0m'
    pos = '\x1b[1m\x1b[32m[+]\x1b[0m'
    shutdown = '\x1b[1m\x1b[31m[!]User requested shutdown...\x1b[0m'
    help_root = '''\nPyIris Help Menu
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
    help_listener = '''\nListener Help Menu
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
    help_scouts = '''\nScouts Help Menu
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
    blacklisted_ip = []
    whitelisted_ip = []
    db_scouts = []
    db_listeners = []
    key = 'LdtwGvWUNeuRqrxCjpMyFEhnOPsISzBbTfQKVAZkDiomlJHgcX'
    End = 'vfyNAiIeoLbExRYCMWzJtXqcDFZlrapVTKgBmUshSjPkGQHdnu'
    globals().update(locals())
