import time as t
import threading as th
from pysettings import tk
from pyperclip import paste as getClip, copy as copyToClip

VERSION = "v1.0"
DESCRIPTION = """
View/Edit your clipboard!


"""

class History:
    def __init__(self, con):
        self.text = con


class ClipBoardGUI(tk.Tk):
    ACTIVE = None
    def __init__(self):
        super().__init__()
        self.forceFocus()
        ClipBoardGUI.ACTIVE = self
        self.onCloseEvent(self.onClose)
        self.setTitle(f"ClipBoard {VERSION}")
        self.closeViaESC()

        self.bind(self.saveClip, tk.EventType.CONTROL_S)

        wx, wy = 450, 145+25

        self.setWindowSize(wx, wy)
        x, y = self.getScreenSize()
        self.setPositionOnScreen(x-wx-10, y-wy-75)

        self.nb = tk.Notebook(self)
        self.clip_nb = self.nb.createNewTab("Clip")
        self.hist_nb = self.nb.createNewTab("History")
        self.nb.placeRelative()

        clip = tk.LabelFrame(self)
        clip.setText("Clipboard")
        clip.placeRelative(changeWidth=-208, changeHeight=-26, changeY=+23, changeX=+2)

        self.hist = tk.LabelFrame(self.hist_nb)
        self.hist.setText("History (1)")
        self.hist.placeRelative(fixWidth=200, stickRight=True)

        self.history = tk.Listbox(self.hist)
        self.history.attachVerticalScrollBar(tk.ScrollBar(self.hist))
        self.history.onSelectEvent(self.historySelect)
        self.history.add("<Current clip>")
        self.history.placeRelative(changeWidth=-5, changeHeight=-30-20)

        tk.Button(self.hist).setText("Clear History").placeRelative(changeWidth=-5, changeY=-20, fixHeight=25, stickDown=True).setCommand(self.clearClipHistory)

        self.text = tk.Text(clip)
        self.text.setWrapping(tk.Wrap.NONE)
        self.text.onUserInputEvent(self.onEdit)
        self.text.placeRelative(changeHeight=-30, changeWidth=-5)

        tools = tk.LabelFrame(self.clip_nb)
        tools.setText("Tools")
        tools.placeRelative(fixWidth=200, stickRight=True)

        self.autoChangeW = tk.Checkbutton(tools).setText("Auto change").setSelected()
        self.autoChangeW.attachToolTip("This option automatically takes over the clipboard into the text field and saves the changes in the clipboard.")
        self.autoChangeW.setTextOrientation()
        self.autoChangeW.onSelectEvent(self.updateWidgets)
        self.autoChangeW.placeRelative(changeWidth=-5, fixHeight=25, fixY=0)
        self.autoChange = True

        self.alwTop = tk.Checkbutton(tools).setSelected()
        self.alwTop.setText("Always on top")
        self.alwTop.setTextOrientation()
        self.alwTop.onSelectEvent(self.updateWidgets)
        self.alwTop.placeRelative(changeWidth=-5, fixHeight=25, fixY=25)

        tk.Button(tools).setText("Clear clipboard").placeRelative(changeWidth=-5, fixHeight=25, fixY=50).setCommand(self.clearClip)
        self.updateClipB = tk.Button(tools).setText("Update clipboard").placeRelative(changeWidth=-5, fixHeight=25, fixY=75).setCommand(self.updateText)
        self.saveClipB = tk.Button(tools).setText("Save clipboard").placeRelative(changeWidth=-5, fixHeight=25, fixY=100).setCommand(self.saveClip)

        self.blockClip = False
        self.oldClip = getClip()
        self.historyList = [History(self.oldClip)]
        self.text.setText(self.oldClip)
        self.content = self.oldClip

        self.waitSaveTimer = t.time()

        self.saved = True
        self.running = True
        #self.updateText()
        self.updateWidgets()
        self.text.setFocus()

        th.Thread(target=self.updateAutoClip).start()

        self.mainloop()

    def updateWidgets(self):
        self.autoChange = self.autoChangeW.getState()
        self.setAllwaysOnTop(self.alwTop.getValue())

        if self.autoChange:
            self.saveClipB.disable()
            self.updateClipB.disable()
            self.setTitle(f"ClipBoard {VERSION}")
            self.saveClip()
            self.saved = True
        else:
            self.saveClipB.enable()
            self.updateClipB.enable()
            if not self.saved:
                self.setTitle(f"*ClipBoard {VERSION}")

    def historySelect(self):
        sel = self.history.getSelectedIndex()
        if sel is None: return
        text = self.historyList[sel].text
        self.text.setText(text)
        self.content = text
        if self.autoChange:
            self.setTitle(f"ClipBoard {VERSION}")
            self.blockClip = True
            self.oldClip = self.content
            copyToClip(text)
            self.blockClip = False
        else:
            self.saved = False
            self.setTitle(f"*ClipBoard {VERSION}")

    def addHistory(self, text):
        if text == "": return
        self.hist.setText(f"History ({len(self.historyList)})")
        self.historyList.insert(0, History(text))
        title = text[:15]+"..." if len(text) > 15 else text
        self.history.add(title, 1)

    def updateAutoClip(self):
        while True:
            t.sleep(.1)
            if not self.running: return
            if self.autoChange:
                if self.blockClip: continue
                clip = getClip()
                if clip != self.oldClip and t.time()-self.waitSaveTimer > 1:
                    self.addHistory(clip)
                    self.text.setText(clip)
                    self.oldClip = clip

    def updateText(self):
        if not self.saved:
            if not tk.SimpleDialog.askYesNo(self, "Do you want do overwrite your changed clip?"):
                return
        self.text.clear()
        clip = getClip()
        if not self.saved or self.oldClip != clip:
            self.addHistory(clip)
            self.text.addText(clip)

    def clearClipHistory(self):
        self.history.clear()
        self.historyList = [self.historyList[0]]
        self.history.add("<Current clip>")
        self.hist.setText(f"History ({0})")

    def saveClip(self):
        self.historyList[0].text = ""
        self.saved = True
        self.setTitle(f"ClipBoard {VERSION}")
        self.blockClip = True
        self.oldClip = self.content
        copyToClip(self.content)
        self.blockClip = False

    def clearClip(self):
        self.blockClip = True
        self.oldClip = self.content
        copyToClip("")
        self.text.clear()
        self.blockClip = False

    def onEdit(self):
        self.waitSaveTimer = t.time()
        _content = self.text.getText()
        if self.content != _content:
            self.content = _content
            if self.autoChange:
                self.saveClip()
            else:
                self.setTitle(f"*ClipBoard {VERSION}")
                self.saved = False

    def onClose(self, e):
        e = tk.Event(e)
        if self.saved:
            self.running = False
            t.sleep(.2)
            ClipBoardGUI.ACTIVE = None
            return
        anw = tk.SimpleDialog.askYesNoCancel(self, "Your clipboard is changed and unsaved!\nDo you want to save the changes?")
        if anw is None:
            e.setCanceled(True)
            return # cancel
        self.running = False
        t.sleep(.2)
        ClipBoardGUI.ACTIVE = None
        if not anw: # no
            return
        else: # yes
            self.saveClip()
            self.running = False
            t.sleep(.2)
            ClipBoardGUI.ACTIVE = None






if __name__ == '__main__':
    ClipBoardGUI()