import socket,cfg,time
from threading import Thread
from modules.banner import *
from modules.wipe import *
from modules.socket_listener import *
from modules.clean import *

cfg.global_variables()

def listener_console():
	while True:
		try:
			input=raw_input(cfg.prompt_listener).strip().split(' ')
			command=input[0]
			if command == 'banner':
				display_banner()
			elif command == 'help':
				print cfg.help_listener
			elif command == 'quit':
				cleanup()
			elif command == 'clear':
				clear()
			elif command == 'back':
				print '\n'+cfg.pos+'Returning...'
				return
			elif command == 'kill':
				killed_thread=False
				try:
					tar_id=int(input[1])
				except:
					print cfg.err+'Argument needs to be a listener ID, eg. "kill 1"'
					continue
				for i in cfg.db_listeners:
					if str(i[0]) == str(tar_id):
						cfg.db_listeners.pop(cfg.db_listeners.index(i))
						print cfg.pos+'Killed active listener with ID : '+str(tar_id)
						killed_thread=True
						break
				if not killed_thread:
					print cfg.err+'Listener of ID "'+str(tar_id)+'" does not exist'
			elif command == 'kill_all':
				print cfg.pos+'Killing all active listeners...'
				cfg.db_listeners=[]
			elif command == 'start':
				try:
					port=int(input[1])
				except:	
					print cfg.err+'Argument needs to be an integer'
					continue
				t=Thread(target=start_listening,args=(port,))
				t.start()
				time.sleep(5)
			elif command == 'show':
				print '\n'+cfg.note+'Currently active listeners :\n'
				if cfg.db_listeners:
					print 'ID\tPort\n==\t===='
					for i in cfg.db_listeners:
						print str(i[0])+'\t'+str(i[1])
					print '\n'
			elif command == '':
				pass
			else:
				print cfg.err+'Unknown command "'+command+'", run "help" for help menu'
		except EOFError:
			try:
				time.sleep(3)
			except KeyboardInterrupt:
				cleanup()
		except KeyboardInterrupt:
			cleanup()
		#except Exception as e:
		#	print cfg.err+'Error running command "'+command+'"  : '+str(e)