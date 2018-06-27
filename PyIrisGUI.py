# Version 0.0.1 By ev-ev
import library.modules.bootstrap as bootstrap
from appJar import gui


def afterRun():
    global app,context
    start = bootstrap.mainGUI(app)
    if start:
        import library.interfaces.home_interface as home_interface
        import library.modules.generator_append as generator_append
        import library.commands.global_interface.clear as clear
        import library.commands.global_interface.quit as quit
        import library.commands.global_interface.python as python
        import library.commands.global_interface.local as local
        import library.commands.global_interface.help as help
        import library.commands.generator_interface.show as show_gen
        import library.commands.generator_interface.reset as reset
        import library.commands.generator_interface.set as set
        import library.commands.generator_interface.load as load
        import library.commands.generator_interface.unload as unload
        import library.commands.generator_interface.generate as generate
        import library.commands.generator_interface.more as more
        app.removeAllWidgets()
        app.setSticky("nesw")
        app.addLabel("title", "PyIris GUI")
        app.setLabelBg("title", "green")
        app.getLabelWidget("title").config(font=("Times", "50", "bold"))

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
        dic=show_gen.mainGUI('options')
        app.setEntry('gen_host', dic['Host'])
        app.setEntry('gen_port', dic['Port'])
        app.setEntry('gen_timeout', dic['Timeout'])
        app.setEntry('gen_windows', dic['Windows'])
        app.setEntry('gen_path', dic['Path'])
        app.addButton("save_gen_options", button_press)



        # start additional panes inside second pane
        app.startPanedFrame("pfv3")
        app.addLabel("Components")
        comp=show_gen.mainGUI('components')
        for component in comp[0]:
            if component=="windows/base" or component=="linux/base":
                pass
            else:
                app.addCheckBox(component)
                app.setCheckBox(component)
        for component in comp[1]:
            if component=="windows/base" or component=="linux/base":
                pass
            else:
                app.addCheckBox(component)


        app.stopPanedFrame()

        # stop second & initial panes
        app.stopPanedFrame()
        app.stopPanedFrame()

        app.startPanedFrame("p2")
        app.addLabel("pf2", "Inside Pane 2")
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
    else:
        pass

def button_press(button):
    pass

if __name__ == "__main__":
    app = gui('PyIris','800x500')
    app.addLabel("title", "PyIris GUI")
    app.setLabelBg("title", "green")
    app.getLabelWidget("title").config(font=("Times","50", "bold"))
    app.setFont(10)
    app.setStartFunction(afterRun)
    app.go()
