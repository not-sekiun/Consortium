import os
import threading


def global_variables():
    scouts_id = 0
    distributed_listener_id = 0
    prompt_default = '\x1b[1m\x1b[37mPyIris > \x1b[0m'
    prompt_listener = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[34mListeners\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    prompt_scouts = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[31mScouts\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    prompt_generator = '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[32mGenerator\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m'
    err = '\x1b[1m\x1b[31m[-]\x1b[0m'
    note = '\x1b[1m\x1b[34m[*]\x1b[0m'
    pos = '\x1b[1m\x1b[32m[+]\x1b[0m'
    user_in = '\x1b[1m\x1b[31m[>]\x1b[0m'
    shutdown = '\x1b[1m\x1b[31m[!]User requested shutdown...\x1b[0m'
    main_help_menu = '''\nMain handler Help Menu
===================

   Global Commands :
      banner                                       Display a banner
      clear                                        Clear the screen
      help                                         Show the help menu
      local <shell command>                        Locally execute a shell command
      python                                       Enter the system python interpreter
      quit                                         Quit the toolkit

   Global settings Commands :
      add <wlist/blist> <IP>                       Add IPs to IP whitelist/blacklist
      change <lkey/skey> <value> [rand]            Change the default current sessions listener key/scout key to something else/ a randomized value
      fake <fake reply>                            Change the default fake reply
      reset <wlist/blist/key/sid/fake_reply> [all] Reset IP whitelist/blacklist, current session server key/scout identifier or all      
      rm <wlist/blist> <IP>                        Remove IPs from IP whitelist/blacklist 
      show                                         Show global variables(IP whitelist/blacklist, current session server key/scout identifier)                       

   Handler Commands :
      generator                                    Change to payload generator handler
      listeners                                    Change to Listeners handler
      scouts                                       Change to Scouts handler\n'''
    listener_help_menu = '''\nListener Handler Help Menu
==========================

   Global Commands :
      banner                      Display a banner
      clear                       Clear the screen
      help                        Show the help menu
      local <shell command>       Locally execute a shell command
      python                      Enter the system python interpreter
      quit                        Quit the framework

   Listener management Commands :
      configs                     Show the configurations of the listener
      kill <ID of Listener> [all] Kill a listener by its ID/Kill all listeners
      reset                       Reset listener configurations
      set <Option> <Value>        Set the value for a specific option to configure the listener
      show                        Show all active listeners
      start                       Start a listener with the set configurations
      
   Handler Commands :   
      back                        Move back to main handler\n'''
    generator_help_menu = '''\nPayload generator Help Menu
==========================
   
   Global Commands :
      banner                         Display a banner
      clear                          Clear the screen
      help                           Show the help menu
      local <shell command>          Locally execute a shell command
      python                         Enter the system python interpreter
      quit                           Quit the framework
   
   Generator payload configuration Commands :
      configs                        Show the configurations of the payload
      generate opt: <path to folder> Generate payload to folder, if no folder given, generates to default sub-folder "deploy"
      reset                          Reset payload configurations
      set <Option> <Value>           Set the value for a specific option to configure the payload
      show                           Show all available payloads 
      use <filename>                 Set configurations for a specific payload by name/change which payload you are generating

   Handler Commands:
      back                           Move back to main handler\n'''
    scout_help_menu = '''\nScouts Help Menu
================
   
   Global Commands :
      banner                            Display a banner
      clear                             Clear the screen
      help                              Show the help menu
      local <shell command>             Locally execute a shell command
      python                            Enter the system python interpreter
      quit                              Quit the framework

   Scout Commands :
      bridge <ID of scout>              Bridge(connect) to a scout to start interacting with it
      kill <ID of scout> [all]          Kill a scout by its ID/Kill all connected scouts
      ping <ID of scout> [all]          Ping a scout by its ID/Ping all scouts
      show                              Show all online scouts
      sleep <ID of scout> [all] <secs>  Sleep a scout/all scouts for a specified amount of seconds

   Handler Commands :
      back                              Move back to main handler\n'''
    blacklisted_ip = []
    whitelisted_ip = []
    db_scouts = []
    db_listeners = []
    f = open('persistent_creds.txt')
    data = f.read().split('\n')
    listener_key = data[0]
    scout_key = data[1]
    untouched_server_key = data[0]
    untouched_scout_identifier = data[1]
    End = data[2]
    framework_version = '0.5.2'
    fake_reply = 'Test Server Running'
    screenlock = threading.Semaphore(value=1)
    current_folder = os.getcwd()
    try:
        os.chdir('payload_templates')
    except (WindowsError,OSError):
        print '[-]payload_templates folder has been tampered with, please reinstall'
    payload_templates_dir = os.getcwd()
    payload_templates_list = os.listdir(payload_templates_dir)
    os.chdir('../')
    globals().update(locals())
