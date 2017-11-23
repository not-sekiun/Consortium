import cfg,socket

cfg.global_variables()

End=cfg.End

def recvall(the_socket):
	total_data=[];data=''
	while True:
		data=the_socket.recv(8192)
		if End in data:
			total_data.append(data[:data.find(End)])
			break
		total_data.append(data)
		if len(total_data)>1:
			last_pair=total_data[-2]+total_data[-1]
			if End in last_pair:
				total_data[-2]=last_pair[:last_pair.find(End)]
				total_data.pop()
				break
	data=''.join(total_data).replace('[+]',cfg.pos).replace('[*]',cfg.note).replace('[-]',cfg.err)
	return data