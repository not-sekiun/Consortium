import os,cfg
from time import sleep
 
cfg.global_variables()

def cleanup():
	try:
		print '\n' + cfg.shutdown
		if cfg.db_scouts:
			try:
				print cfg.note+'Disconnecting all scouts...'
				for i in cfg.db_scouts:
					try:
						i[5].sendall('sleep 60'+cfg.End)
					except socket.error:
						pass
				print cfg.note+'Scouts are disconnected'
			except:
				print cfg.err+'Error disconnecting scouts'
			print cfg.pos+'Done'
		cfg.db_listeners=[]
		print cfg.note+'Killing all active listeners...'
		sleep(5)
		print cfg.pos+'Done'
		print cfg.note+'Exiting program...'
		os._exit(1)
	except EOFError:
		try:
			time.sleep(3)
		except KeyboardInterrupt:
			cleanup()
	except KeyboardInterrupt:
			print cfg.err+'SKIPPING ALL CLEANUP STEPS!!!'
			os._exit(1)