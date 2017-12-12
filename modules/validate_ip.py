import socket

def validate_ip(tar_ip):
	try:
		socket.inet_aton(tar_ip)
		return True
	except:
		return False
