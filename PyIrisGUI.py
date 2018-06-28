# Version 0.0.1 By ev-ev
import library.modules.bootstrap as bootstrap
from appJar import gui
import os
import library.modules.config as config
import library.interfaces.home_interface as home_interface
import library.modules.generator_append as generator_append
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.generator_interface.show as show_gen
import library.commands.generator_interface.reset as reset
import library.commands.generator_interface.set as set_gen
import library.commands.generator_interface.load as load_gen
import library.commands.generator_interface.unload as unload_gen
import library.commands.generator_interface.generate as generate
import library.commands.generator_interface.more as more

def label(app):
    app.setSticky("nesw")
    app.addLabel("title", "PyIris GUI")
    app.setLabelBg("title", "green")
    app.getLabelWidget("title").config(font=("Times", "50", "bold"))

def main(app):

    app.startTabbedFrame("TabbedFrame")
    app.startTab("Home")
    app.addLabel("Home menu")
    app.stopTab()
    app.startTab("Generators")
    app.addLabel("Generator Menu")
    app.startPanedFrameVertical("pfv1")
    app.startPanedFrame("p1")
    app.setBg('orange')
    app.addLabel("Settings and etc.")

    # start second, vertical pane inside initial pane
    app.startPanedFrameVertical("pfv2")
    app.addLabel("Options")
    app.addLabelEntry("gen_host")
    app.addLabelEntry("gen_port")
    app.addLabelEntry("gen_timeout")
    app.addLabelEntry("gen_windows")
    app.addLabelEntry("gen_path")
    dic = show_gen.mainGUI('options')
    app.setEntry('gen_host', dic['Host'])
    app.setEntry('gen_port', dic['Port'])
    app.setEntry('gen_timeout', dic['Timeout'])
    app.setEntry('gen_windows', dic['Windows'])
    app.setEntry('gen_path', dic['Path'])
    app.addButton("save_gen_options", button_press)

    # start additional panes inside second pane
    app.startPanedFrame("pfv3")
    app.addLabel("Components")
    comp = show_gen.mainGUI('components')
    for component in comp[0]:
        if component == "windows/base" or component == "linux/base":
            pass
        else:
            app.addCheckBox(component)
            app.setCheckBox(component)
    for component in comp[1]:
        if component == "windows/base" or component == "linux/base":
            pass
        else:
            app.addCheckBox(component)
    app.addButton("save_gen_components", button_press)

    app.stopPanedFrame()

    # stop second & initial panes
    app.stopPanedFrame()
    app.stopPanedFrame()

    app.startPanedFrame("p2")
    app.setBg('orange')
    app.addLabel("Execute python and batch")

    app.startPanedFrame("aaa")
    app.addLabel('py',"Python 2")
    app.addNamedButton('Start python 2 interpreter','exec_py_code',button_press)


    app.startPanedFrame("bbb")
    app.addLabel("Local")
    app.addEntry("exec_cmd_code_input")
    app.setEntryDefault('exec_cmd_code_input','Enter cmd code here')
    app.addMessage("exec_cmd_code_output",'')
    #app.setMessageWidth('exec_cmd_code_output', 1000)
    app.addNamedButton('Execute code', 'exec_cmd_code', button_press)
    app.stopPanedFrame()

    app.stopPanedFrame()
    app.stopPanedFrame()

    app.startPanedFrame("p3")
    app.addLabel("pf3", "Inside Pane 3")
    app.stopPanedFrame()

    app.stopPanedFrame()
    app.stopTab()

    app.startTab("Listeners")
    app.addLabel("Listener Menu")
    app.stopTab()

    app.startTab("Scouts")
    app.addLabel("Scouts Menu")
    app.stopTab()

    app.stopTabbedFrame()
def refresh(app):
    tab=app.getTabbedFrameSelectedTab("TabbedFrame")
    app.removeAllWidgets()
    label(app)
    main(app)
    app.setTabbedFrameSelectedTab('TabbedFrame', tab)
def afterRun():
    global app,context
    start = bootstrap.mainGUI(app)
    if start:
        app.removeAllWidgets()
        label(app)
        main(app)
    else:
        pass

def button_press(button):
    if button == "save_gen_options":
        host=app.getEntry("gen_host")
        port=app.getEntry("gen_port")
        timeout=app.getEntry("gen_timeout")
        windows=app.getEntry("gen_windows")
        path=app.getEntry("gen_path")
        if windows!="True" and windows!="False":
            app.addLabel("input_win_error","Windows is set to an invalid value")
            app.setLabelBg("input_win_error","red")
            return
        set_gen.mainGUI('set Host '+host)
        set_gen.mainGUI('set Port '+port)
        set_gen.mainGUI('set Timeout '+timeout)
        set_gen.mainGUI('set Windows '+windows)
        set_gen.mainGUI('set Path '+path)
        refresh(app)
    if button == "save_gen_components":
        cbs=app.getAllCheckBoxes()
        for o,v in cbs.items():
            if 'windows/' in o or 'linux/' in o:
                if v == True:
                    load_gen.mainGUI('load '+o)
                else:
                    unload_gen.mainGUI('unload '+o)
        refresh(app)
    if button == "exec_py_code":
        os.system('start py -2')
        refresh(app)
    if button == "exec_cmd_code":
        code=app.getEntry('exec_cmd_code_input')
        refresh(app)
        res=local.mainGUI('local '+code).replace('\n','')
        app.setMessage('exec_cmd_code_output',res)


if __name__ == "__main__":
    app = gui('PyIris','1000x800')
    app.addLabel("title", "PyIris GUI")
    app.setLabelBg("title", "green")
    app.getLabelWidget("title").config(font=("Times","50", "bold"))
    app.setFont(10)
    app.setStartFunction(afterRun)
    app.go()
