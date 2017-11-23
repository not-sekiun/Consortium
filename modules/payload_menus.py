def payload_help_menus(payload_name):
    help_command_shell = '''\nCommand Shell Menu
==================

   Global Commands :
      banner                            Display a banner
      help                              Show the help menu
      quit                              Quit the console
      clear                             Clear the screen
 
   Connection commands :
      disconnect                        Make the scout disconnect and try to reconnect
      terminate                         Kill tbe scout process
      sleep <seconds>                   Disconnect the scout and make it sleep for some time

   Command Shell Commands :
      exec <shell command>              Executes shell command and returns output
      exec_file <file/executable>       Executes a file/executable
      toggle                            toggle whether commands are run by powershell or cmd
 
   File Commands :
      download <filepath>               Download file
      dump <filepath>                   Dump and view file content(supports .docx file)
      upload <filepath>                 Upload a file
      web_download <url>                Download a file through a url
    
   Note :
      Upload and download replace spaces in file names with underscores\n'''
    mapper={'Command Shell':help_command_shell}
    help_menu=mapper[payload_name]
    return help_menu