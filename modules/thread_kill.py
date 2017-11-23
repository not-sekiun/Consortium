import cfg

cfg.global_variables()

def kill_listener_thread(id):
	for i in cfg.db_listeners:
		if str(i[0]) == id:
			return True
	return False