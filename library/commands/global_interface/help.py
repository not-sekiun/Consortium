import library.modules.config as config

config.main()

home_help = '''
Home Interface Help Menu
========================
   Global Commands :
      clear            Clear the screen
      help             Show the help menu or help for specific command, alias of the command is "?"
      local            Locally execute a command, alias of the command is "!"
      python           Open up a local python interpreter
      quit             Quit the framework
   
   Global settings :
      add              Add a hostname to the hostname whitelist or blacklist
      regen            Initiate a manual key generation, will overwrite existing key
      reset            Reset the hostname whitelist or blacklist
      rm               Remove a hostname from the hostname whitelist or blacklist
      show             Show the hostname whitelist and blacklist
   
   Interface Commands:
      generator        Change to the generator interface
      listeners        Change to the listener interface
      scouts           Change to the scouts interface
'''
listener_help = '''
Listener Interface Help Menu
============================
   Global Commands :
      clear             Clear the screen
      help              Show the help menu or help for specific command, alias of the command is "?"
      local             Locally execute a command, alias of the command is "!"
      python            Open up a local python interpreter
      quit              Quit the framework

   Listener Commands :
      bind              Connect to a scout that is using a bind connection
      kill              Kill a listener
      more              Show more information for a listener
      rename            Rename a listener by its ID
      reset             Reset an option to the default value
      run               Start a listener with the currently set options
      set               Set an option to a value
      show              Show the current configurations of a listener that is being set or active listeners

   Interface Commands :
      back              Return to the home interface
'''
scout_help = '''
Scout Interface Help Menu
=========================
   Global Commands :
      clear             Clear the screen
      help              Show the help menu or help for specific command, alias of the command is "?"
      local             Locally execute a command, alias of the command is "!"
      python            Open up a local python interpreter
      quit              Quit the framework
   
   Scout Commands:
      bridge            Bridge to a specific scout
      disconnect        Disconnect a scout
      kill              Kill a scout
      more              Get more info about a scout
      ping              Ping a scout
      rename            Rename a scout by its ID
      show              Show all currently connected scouts
      sleep             Make a scout disconnect and sleep for a specified amount of time

   Interface Commands :
      back              Return to the home interface
'''
generator_help = '''
Generator Interface Help Menu
========================
   Global Commands :
      clear             Clear the screen
      help              Show the help menu or help for specific command, alias of the command is "?"
      local             Locally execute a command, alias of the command is "!"
      python            Open up a local python interpreter
      quit              Quit the framework
   
   Generator Commands :
      generate          Start the scout generation
      load_com          Load a component in the generator
      load_enc          Load an encoder in the generator
      more_com          Show more info for a component
      more_enc          Show more info for an encoder
      reset             Reset an option to the default value
      set               Set an option to a value
      show              Show all loadable components or options
      unload_com        Unload a component in the generator
      unload_enc        Unload an encoder in the generator
   
   Interface Commands :
      back              Return to the home interface
'''


def home(command):
    if command == 'add':
        print '\nUsage       : add ["wh"|"bl"] <h>' \
              '\nDescription : Add a hostname to the hostname blacklist or whitelist' \
              '\nOptions     : "wh"  : Add to the hostname whitelist' \
              '\n              "bl"  : Add to the hostname blacklist' \
              '\n              <h>   : The hostname to add to the lists\n'
    elif command == 'clear':
        print '\nUsage       : clear' \
              '\nDescription : Clears the screen\n'
    elif command == 'generator':
        print '\nUsage       : generator' \
              '\nDescription : Switch to the generator interface\n'
    elif command == 'help':
        print '\nUsage       : help [opt : <c>]' \
              '\nDescription : Displays the help for a command or the general help menu if no value is provided' \
              '\nOptions     : <c> : The valid name of a command that can be executed in the current handler\n'
    elif command == 'listeners':
        print '\nUsage       : listeners' \
              '\nDescription : Switch to the listener interface\n'
    elif command == 'local':
        print '\nUsage       : local <c>' \
              '\nDescription : Locally executes a shell command and displays the output' \
              '\nOptions     : <c> : A command to execute locally on the system\n'
    elif command == 'python':
        print '\nUsage       : python' \
              '\nDescription : Enters the systems local python interpreter\n'
    elif command == 'quit':
        print '\nUsage       : quit' \
              '\nDescription : Quits the framework\n'
    elif command == 'regen':
        print '\nUsage       : regen' \
              '\nDescription : Manually initiate a key generation, overwriting existing key file\n'
    elif command == 'reset':
        print '\nUsage       : reset ["wh"|"bl"|"all"]' \
              '\nDescription : Reset and clear the hostname blacklist or whitelist' \
              '\nOptions     : "wh"  : Reset the hostname whitelist' \
              '\n              "bl"  : Reset the hostname blacklist' \
              '\n              "all" : Reset both hostname blacklist and whitelist\n'
    elif command == 'rm':
        print '\nUsage       : rm ["wh"|"bl"] <h>' \
              '\nDescription : Remove a hostname from the hostname blacklist or whitelist' \
              '\nOptions     : "wh"  : Remove from the hostname whitelist' \
              '\n              "bl"  : Remove from the hostname blacklist' \
              '\n              <h>   : The hostname to remove from the lists\n'
    elif command == 'scouts':
        print '\nUsage       : scouts' \
              '\nDescription : Switch to the scout interface\n'
    elif command == 'show':
        print '\nUsage       : show ["wh"|"bl"|"all"|"key"]' \
              '\nDescription : Show the hostname blacklist, whitelist, both, or listener key' \
              '\nOptions     : "wh"  : Show the hostname whitelist' \
              '\n              "bl"  : Show the hostname blacklist' \
              '\n              "all" : Show both the hostname blacklist and whitelist' \
              '\n              "key" : Show the currently used listener key'
    elif command == '?':
        print '\nAn alias for the command "help"\n'
    elif command == '!':
        print '\nAn alias for the command "local"\n'
    else:
        print config.neg + 'Please enter a valid command'


def listener(command):
    if command == 'back':
        print '\nUsage       : back' \
              '\nDescription : Return to the home interface\n'
    elif command == 'bind':
        print '\nUsage       : bind <host> <port>' \
              '\nDescription : Connects to a scout using a bind connection protocol' \
              '\nOptions     : <host> : Hostname of scout' \
              '\n              <port> : Port number that remote scout has opened\n'
    elif command == 'clear':
        print '\nUsage       : clear' \
              '\nDescription : Clears the screen\n'
    elif command == 'help':
        print '\nUsage       : help [opt : <c>]' \
              '\nDescription : Displays the help for a command or the general help menu if no value is provided' \
              '\nOptions     : <c> : The valid name of a command that can be executed in the current handler\n'
    elif command == 'kill':
        print '\nUsage       : kill [<i>|"all"]' \
              '\nDescription : Kills a listener by its ID' \
              '\nOptions     : <i>   : ID of listener to kill' \
              '\n              "all" : Kill all listeners\n'
    elif command == 'local':
        print '\nUsage       : local <c>' \
              '\nDescription : Locally executes a shell command and displays the output' \
              '\nOptions     : <c> : A command to execute locally on the system\n'
    elif command == 'more':
        print '\nUsage       : more [<i>|"all"]' \
              '\nDescription : Show more information for a listener by its ID or for all listeners' \
              '\nOptions     : <i>   : ID of the listener to show more information of' \
              '\n              "all" : Show information for all listeners\n'
    elif command == 'python':
        print '\nUsage       : python' \
              '\nDescription : Enters the systems local python interpreter\n'
    elif command == 'quit':
        print '\nUsage       : quit' \
              '\nDescription : Quits the framework\n'
    elif command == 'rename':
        print '\nUsage       : rename <i> <n>' \
              '\nDescription : Rename a listener by ID' \
              '\nOptions     : <i> : ID of listener to rename' \
              '\n              <n> : New name of the listener\n'
    elif command == 'reset':
        print '\nUsage       : reset [<o>|"all"]' \
              '\nDescription : Reset a set option to the default value' \
              '\nOptions     : <o>   : Option to reset the value for' \
              '\n              "all" : Reset all options\n'
    elif command == 'run':
        print '\nUsage       : run' \
              '\nDescription : Starts a listener with the options the user has set using the "set" command\n'
    elif command == 'set':
        print '\nUsage       : set <o> <v>' \
              '\nDescription : Set an option to a specific value' \
              '\nOptions     : <o> : The valid option of a listener that can be set' \
              '\n              <v> : The value to set that option to\n'
    elif command == 'show':
        print '\nUsage       : show ["options"|"listeners"]' \
              '\nDescription : Show the current configurations of a listener that is being set' \
              '\nOptions     : "options"   : Show the currently set options of a listener' \
              '\n              "listeners" : Show all active listeners\n'
    elif command == '?':
        print '\nAn alias for the command "help"\n'
    elif command == '!':
        print '\nAn alias for the command "local"\n'
    else:
        print config.neg + 'Please enter a valid command'


def scout(command):
    if command == 'back':
        print '\nUsage       : back' \
              '\nDescription : Return to the home interface\n'
    elif command == 'bridge':
        print '\nUsage       : bridge <i>' \
              '\nDescription : Bridge to a scout and directly interact with it' \
              '\nOptions     : <i> : The ID of the scout to show more info for\n'
    elif command == 'clear':
        print '\nUsage       : clear' \
              '\nDescription : Clears the screen\n'
    elif command == 'disconnect':
        print '\nUsage       : disconnect (<i>|"all")' \
              '\nDescription : Disconnect a scout from the listeners' \
              '\nOptions     : <i>   : The ID of the scout to disconnect (scout sleeps for 3 seconds before reconnecting)' \
              '\n              "all" : Disconnect all scouts (all sleep for 3 seconds before reconnecting)\n'
    elif command == 'help':
        print '\nUsage       : help [opt : <c>]' \
              '\nDescription : Displays the help for a command or the general help menu if no value is provided' \
              '\nOptions     : <c> : The valid name of a command that can be executed in the current handler\n'
    elif command == 'kill':
        print '\nUsage       : kill (<i>|"all")' \
              '\nDescription : Kill a scout, force it to exit and terminate itself remotely' \
              '\nOptions     : <i>   : The ID of the scout to kill' \
              '\n              "all" : Kill all scouts\n'
    elif command == 'local':
        print '\nUsage       : local <c>' \
              '\nDescription : Locally executes a shell command and displays the output' \
              '\nOptions     : <c> : A command to execute locally on the system\n'
    elif command == 'more':
        print '\nUsage       : more [<i>|"all"]' \
              '\nDescription : Show more information for a scout by its ID or for all scoutsmore ' \
              '\nOptions     : <i>   : ID of the scout to show more information of' \
              '\n              "all" : Show information for all scouts\n'
    elif command == 'ping':
        print '\nUsage       : ping (<i>|"all")' \
              '\nDescription : Ping a scout' \
              '\nOptions     : <i>   : The ID of the scout to ping' \
              '\n              "all" : Ping all scouts'
    elif command == 'python':
        print '\nUsage       : python' \
              '\nDescription : Enters the systems local python interpreter\n'
    elif command == 'quit':
        print '\nUsage       : quit' \
              '\nDescription : Quits the framework\n'
    elif command == 'rename':
        print '\nUsage       : rename <i> <n>' \
              '\nDescription : Rename a scout by ID' \
              '\nOptions     : <i> : ID of scout to rename' \
              '\n              <n> : New name of the scout\n'
    elif command == 'sleep':
        print '\nUsage       : sleep (<i>|"all") <t>' \
              '\nDescription : Scout will disconnect and sleep for a specified amount of time before reconnecting to the listeeners' \
              '\nOptions     : <i>   : The ID of the scout to sleep' \
              '\n              <t>   : An integer in seconds to specify how long to sleep the scout' \
              '\n              "all" : Sleep all scouts for a specific amount of time\n'
    elif command == 'show':
        print '\nUsage       : show ["scouts"]' \
              '\nDescription : Show all scouts that are connected' \
              '\nOptions     : "scouts" : Show all scouts that are connected\n'
    elif command == '?':
        print '\nAn alias for the command "help"\n'
    elif command == '!':
        print '\nAn alias for the command "local"\n'
    else:
        print config.neg + 'Please enter a valid command'


def generator(command):
    if command == 'back':
        print '\nUsage       : back' \
              '\nDescription : Return to the home interface\n'
    elif command == 'clear':
        print '\nUsage       : clear' \
              '\nDescription : Clears the screen\n'
    elif command == 'generate':
        print '\nUsage       : generate' \
              '\nDescription : Start scout generation after loading on desired library\n'
    elif command == 'help':
        print '\nUsage       : help [opt : <c>]' \
              '\nDescription : Displays the help for a command or the general help menu if no value is provided' \
              '\nOptions     : <c> : The valid name of a command that can be executed in the current handler\n'
    elif command == 'load_com':
        print '\nUsage       : load_com [<n>|<i>|"all"]' \
              '\nDescription : Load a component to generate a scout with' \
              '\nOptions     : <n>   : Name of a valid component to load' \
              '\n              <i>   : ID of a valid component to load' \
              '\n              "all" : Load all components\n'
    elif command == 'load_enc':
        print '\nUsage       : load_enc [<n>|<i>|"all"]' \
              '\nDescription : Load an encoder to encode and encrypt a scout with' \
              '\nOptions     : <n>   : Name of a valid component to load' \
              '\n              <i>   : ID of a valid component to load\n'
    elif command == 'local':
        print '\nUsage       : local <c>' \
              '\nDescription : Locally executes a shell command and displays the output' \
              '\nOptions     : <c> : A command to execute locally on the system\n'
    elif command == 'more_com':
        print '\nUsage       : more_com [<n>|<i>]' \
              '\nDescription : Show more advanced info for a scout component' \
              '\nOptions     : <n> : The name of the component to show more info for' \
              '\n              <i> : The ID of the component to shoe more info for\n'
    elif command == 'more_enc':
        print '\nUsage       : more_enc [<n>|<i>]' \
              '\nDescription : Show more advanced info for a scout encoder' \
              '\nOptions     : <n> : The name of the component to show more info for\n'
    elif command == 'python':
        print '\nUsage       : python' \
              '\nDescription : Enters the systems local python interpreter\n'
    elif command == 'quit':
        print '\nUsage       : quit' \
              '\nDescription : Quits the framework\n'
    elif command == 'reset':
        print '\nUsage       : reset [<o>|"all"]' \
              '\nDescription : Reset a set option to the default value' \
              '\nOptions     : <o>   : Option to reset the value for' \
              '\n              "all" : Reset all options\n'
    elif command == 'set':
        print '\nUsage       : set <o> <v>' \
              '\nDescription : Set an option to a specific value' \
              '\nOptions     : <o> : The valid option of a listener that can be set' \
              '\n              <v> : The value to set that option to\n'
    elif command == 'show':
        print '\nUsage       : show ["options"|"components"|"loaded"|"encoders"]' \
              '\nDescription : Show all mutable options or loadable components' \
              '\nOptions     : "options"    : Options that can be changed' \
              '\n              "components" : All loadable scout components' \
              '\n              "loaded"     : All currently loaded scout components' \
              '\n              "encoders"   : All useable encoders\n'
    elif command == 'unload_com':
        print '\nUsage       : unload_com [<n>|<i>|"all"]' \
              '\nDescription : Unload a component to generate a scout with' \
              '\nOptions     : <n>   : Name of a valid component to unload' \
              '\n              <i>   : ID of a valid component to unload' \
              '\n              "all" : Unload all components\n'
    elif command == 'unload_enc':
        print '\nUsage       : unload_enc [<n>|<i>|"all"]' \
              '\nDescription : Unload an encoder that encodes and encrypts a scout' \
              '\nOptions     : <n>   : Name of a valid component to unload' \
              '\n              <i>   : ID of a valid component to unload' \
              '\n              "all" : Unload all components\n'
    elif command == '?':
        print '\nAn alias for the command "help"\n'
    elif command == '!':
        print '\nAn alias for the command "local"\n'
    else:
        print config.neg + 'Please enter a valid command'


def main(interface, command):
    command = command.split(' ')
    filter(lambda a: a != '', command)
    if interface == 'home':
        try:
            home(command[1])
        except IndexError:
            print home_help
    elif interface == 'listener':
        try:
            listener(command[1])
        except IndexError:
            print listener_help
    elif interface == 'scout':
        try:
            scout(command[1])
        except IndexError:
            print scout_help
    elif interface == 'generator':
        try:
            generator(command[1])
        except IndexError:
            print generator_help
