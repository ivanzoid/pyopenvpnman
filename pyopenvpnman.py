import wx
import os
import sys
import subprocess
import socket, asyncore, asynchat
from datetime import datetime

from authdlg import *
from logdlg import *

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()
id_REFRESH = wx.NewId()
id_ABOUT = wx.NewId()

def escapePassword(password):
    result = password.replace('\\', '\\\\').replace('"', '\\"').replace(' ', '\\ ')
    return result

class ManagementInterfaceHandler(asynchat.async_chat):
    def __init__(self, mainwnd, addr, port):
        asynchat.async_chat.__init__(self)
        #print 'ManagementInterfaceHandler construct'
        self.mainwnd = mainwnd
        self.port = port
        self.buf = ''
        self.set_terminator('\n')
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((addr, port))
        
    def handle_connect(self):
        #print 'handle_connect ({0})'.format(self.port)
        asynchat.async_chat.handle_connect(self)
        
    def handle_close(self):
        #print 'handle_close'
        self.mainwnd.Disconnected(self.port)
        asynchat.async_chat.handle_close(self)
    
    def collect_incoming_data(self, data):
        #print 'collect_incoming_data ({0}) data: "{1}"'.format(self.port, data)
        self.buf += data
        
    def found_terminator(self):
        #print 'found_terminator ({0}) buf: "{1}"'.format(self.port, self.buf)
        if self.buf.startswith(">PASSWORD:Need 'Auth'"):
            authdlg = AuthDlg(self.mainwnd)
            if authdlg.ShowModal() == wx.ID_OK:
                username = authdlg.username.GetValue()
                password = authdlg.password.GetValue()
                self.send('username "Auth" {0}\n'.format(username))
                self.send('password "Auth" "{0}"\n'.format(escapePassword(password)))
            authdlg.Destroy()
        elif self.buf.startswith('>HOLD:Waiting for hold release'):
            self.send('log on all\n') # enable logging and dump current log contents
            self.send('state on all\n') # ask openvpn to automatically report its state and show current
            self.send('hold release\n') # tell openvpn to continue its start procedure
        elif self.buf.startswith('>LOG:'):
            self.mainwnd.GotLogLine(self.port, self.buf[5:])
        elif self.buf.startswith('>STATE:'):
            self.mainwnd.GotStateLine(self.port, self.buf[7:])
        self.buf = ''
    
# 'enum' of connection states
(disconnected, failed, connecting, disconnecting, connected) = range(5)

class Connection(object):
    def __init__(self, name):
        self.name = name
        self.state = disconnected # do not set this field directly, use MainWindow.setConnState()
        self.sock = None # ManagementInterfaceHandler
        self.port = 0
        self.logbuf = []
        self.logdlg = None # LogDlg
    def stateString(self):
        if self.state == disconnected:
            return 'Disconnected'
        elif self.state == failed:
            return 'Error'
        elif self.state == connecting:
            return 'Connecting'
        elif self.state == disconnecting:
            return 'Disconnecting'
        elif self.state == connected:
            return 'Connected'
        else:
            return 'Error'
        
def getBasePath():
    if hasattr(sys, "frozen") and sys.frozen == "windows_exe":
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(400,300))
        
        # check cmdline options
        
        self.ovpnpath = 'C:\\Program Files\\OpenVPN'
        
        if len(sys.argv) == 3:
            if sys.argv[1] == '--openvpn':
                self.ovpnpath = sys.argv[2]


        self.path = getBasePath() + '/'                 
        self.ovpnconfigpath = self.ovpnpath + '\\config'
        self.ovpnexe = self.ovpnpath + '\\bin\\openvpn.exe'
        self.traymsg = 'OpenVPN Connection Manager'

        self.connections = {}

        # set app icon
        self.SetIcon(wx.Icon(self.path + 'images/app.ico', wx.BITMAP_TYPE_ICO))

        # init tray icon

        self.notconnectedIcon = wx.Icon(self.path + 'images/fail16.ico', wx.BITMAP_TYPE_ICO)
        self.waitingIcon = wx.Icon(self.path + 'images/waiting16.ico', wx.BITMAP_TYPE_ICO)
        self.connectedIcon = wx.Icon(self.path + 'images/ack16.ico', wx.BITMAP_TYPE_ICO)

        self.trayicon = wx.TaskBarIcon()
        self.trayicon.SetIcon(self.notconnectedIcon, self.traymsg)

        self.wndshown = True

        self.Bind(wx.EVT_ICONIZE, self.OnIconize)
        self.trayicon.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTrayIconClick)

        # init toolbar

        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_TEXT)

        connectBtn = self.toolbar.AddLabelTool(id_CONNECT, 'Connect', bitmap=wx.Bitmap(self.path + 'images/connect32.png'))
        disconnectBtn = self.toolbar.AddLabelTool(id_DISCONNECT, 'Disconnect', bitmap=wx.Bitmap(self.path + 'images/disconnect32.png'))
        editcfgBtn = self.toolbar.AddLabelTool(id_EDITCFG, 'Edit config', wx.Bitmap(self.path + 'images/editcfg32.png'))
        viewlogBtn = self.toolbar.AddLabelTool(id_VIEWLOG, 'View log', bitmap=wx.Bitmap(self.path + 'images/viewlog32.png'))
        refreshBtn = self.toolbar.AddLabelTool(id_REFRESH, 'Refresh', wx.Bitmap(self.path + 'images/refresh32.png'), shortHelp='Reread OpenVPN config files list')
        aboutBtn = self.toolbar.AddLabelTool(id_ABOUT, 'About', wx.Bitmap(self.path + 'images/about32.png'))

        self.Bind(wx.EVT_TOOL, self.OnCmdConnect, connectBtn, id_CONNECT)
        self.Bind(wx.EVT_TOOL, self.OnCmdDisconnect, disconnectBtn, id_DISCONNECT)
        self.Bind(wx.EVT_TOOL, self.OnCmdEditCfg, editcfgBtn, id_EDITCFG)
        self.Bind(wx.EVT_TOOL, self.OnCmdViewLog, viewlogBtn, id_VIEWLOG)
        self.Bind(wx.EVT_TOOL, self.OnCmdRefresh, refreshBtn, id_REFRESH)
        self.Bind(wx.EVT_TOOL, self.OnCmdAbout, aboutBtn, id_ABOUT)

        self.toolbar.Realize()

        self.toolbar.EnableTool(id_CONNECT, False)
        self.toolbar.EnableTool(id_DISCONNECT, False)
        self.toolbar.EnableTool(id_EDITCFG, False)
        self.toolbar.EnableTool(id_VIEWLOG, False)

        # init list view

        self.imgs = wx.ImageList(24, 24, mask=True)
        self.disconnectedImgId = self.imgs.Add(wx.Bitmap(self.path + 'images/disconnected24.png'))
        self.connectedImgId = self.imgs.Add(wx.Bitmap(self.path + 'images/connected24.png'))
        self.waitingImgId = self.imgs.Add(wx.Bitmap(self.path + 'images/waiting24.png'))

        self.list = wx.ListCtrl(self, -1, style=(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES))
        self.list.SetImageList(self.imgs, wx.IMAGE_LIST_SMALL)

        self.list.InsertColumn(0, '')
        self.list.InsertColumn(1, 'Name')
        self.list.InsertColumn(2, 'Status')

        self.updateList()

        self.list.SetColumnWidth(0, 29)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(2, wx.LIST_AUTOSIZE)

        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)

        self.list.Focus(0)
        self.list.Select(0)

        # create timer which will poll incoming data from sockets to 
        # our ManagementInterfaceHandler
        self.timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(20, wx.TIMER_CONTINUOUS)

    def imgIndexByState(self, state):
        """Returns image index from the imagelist to be used in listctrl in list of connctions corresponding to the given state of connection."""        
        if state == disconnected or state == failed:
            return self.disconnectedImgId
        elif state == connecting or state == disconnecting:
            return self.waitingImgId
        elif state == connected:
            return self.connectedImgId
        else: # ?
            return -1

    def getConnList(self, path):
        """Returns list of connections in the OpenVPN's config directory."""
        if not os.path.exists(path):
            return []
        files = os.listdir(path)
        ovpnfiles = filter(lambda s: s.endswith('.ovpn'), files)
        ovpnnames = map(lambda s: s[:-5], ovpnfiles)
        return ovpnnames

    def updateList(self):
        """Updates list of connections in the main window."""
        # save all previous (current) connections to a dict of pairs name:connection
        prevconns = {}
        for c in self.connections.itervalues():
            prevconns[c.name] = c

        # get list of new connections
        newlist = self.getConnList(self.ovpnconfigpath)
        # delete listctrl contents
        self.list.DeleteAllItems()
        self.connections.clear()
        for i, s in enumerate(newlist):
            if s in prevconns: # check if this connection existed previously
                self.connections[i] = prevconns[s]
            else:
                self.connections[i] = Connection(s)
            self.list.InsertStringItem(i, '', self.imgIndexByState(self.connections[i].state))
            self.list.SetStringItem(i, 1, s)
            self.list.SetStringItem(i, 2, self.connections[i].stateString())

    def updateConnection(self, index):
        """Updates connection's list item given by its index."""
        if index != -1:
            self.list.SetItemImage(index, self.imgIndexByState(self.connections[index].state))
            self.list.SetStringItem(index, 2, self.connections[index].stateString())

    def updateToolbar(self, index):
        """Repaints toolbar based on selected connection and its state."""
        if index == -1:
            self.toolbar.EnableTool(id_CONNECT, False)
            self.toolbar.EnableTool(id_DISCONNECT, False)
            self.toolbar.EnableTool(id_EDITCFG, False)
            self.toolbar.EnableTool(id_VIEWLOG, False)
        else: # have selected item
            self.toolbar.EnableTool(id_EDITCFG, True)            
            if self.connections[index].state == disconnected \
            or self.connections[index].state == failed:
                self.toolbar.EnableTool(id_CONNECT, True)
                self.toolbar.EnableTool(id_DISCONNECT, False)
            else:
                self.toolbar.EnableTool(id_CONNECT, False)
                self.toolbar.EnableTool(id_DISCONNECT, True)
            if self.connections[index].logdlg != None:
                self.toolbar.EnableTool(id_VIEWLOG, False)
            else:
                self.toolbar.EnableTool(id_VIEWLOG, True)

    def maybeUpdateToolbar(self, index):
        """Checks if connection supplied by index is current and in that case repaints it."""
        curindex = self.list.GetFocusedItem()
        if curindex == index:
            self.updateToolbar(index)

    def OnItemSelected(self, event):
        self.updateToolbar(event.m_itemIndex)

    def OnItemDeselected(self, event):
        if self.list.GetSelectedItemCount() == 0:
            self.updateToolbar(-1)

    def trayIconByState(self, state):
        """Return corresponding wx.Icon for tray depending on the given state of connection."""
        if state == connecting or state == disconnecting:
            return self.waitingIcon
        elif state == connected:
            return self.connectedIcon
        else:
            return self.notconnectedIcon

    def updateTrayIcon(self):
        """Updates tray icon. If there are at least one 'conected' connection, shows 'connected' icon, otherwise shows 'disconnected' icon."""
        maxstate = disconnected
        for c in self.connections.itervalues():
            if c.state > maxstate:
                maxstate = c.state
        self.trayicon.SetIcon(self.trayIconByState(maxstate), self.traymsg)

    def OnIconize(self, event):
        """Called when user clicks minimize button."""
        self.Hide()
        self.wndshown = False

    def OnTrayIconClick(self, event):
        if self.wndshown:
            self.Hide()
            self.wndshown = False
        else:
            self.Iconize(False)
            self.Show(True)
            self.Raise()
            self.wndshown = True

    def setConnState(self, index, state):
        """Sets the state of connection given by index (which is its Id from listctrl) and updates trayicon if necessary."""
        self.connections[index].state = state
        if state == disconnected:
            self.connections[index].port = 0
        if state == connected:
            self.trayicon.SetIcon(self.trayIconByState(state), self.traymsg)
        else:
            self.updateTrayIcon()

    def OnTimer(self, event):
        """Used for detecting if there is incoming data in the sockets."""
        asyncore.poll(timeout=0)

    def getNextAvailablePort(self):
        """Returns next minimal unused port starting from 10598."""
        minport = 10598
        found = False
        while not found:
            found = True
            for c in self.connections.itervalues():
                if c.port != 0:
                    if c.port == minport:
                        found = False
                        minport += 1
                        break
        return minport

    def indexFromPort(self, port):
        """Returns index (id) of connected connection based on its port."""
        for i, c in self.connections.iteritems():
            if c.port == port:
                return i
        return -1

    def OnCmdConnect(self, event):
        #print 'OnCmdConnect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        port = self.getNextAvailablePort()
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen([self.ovpnexe,
                          '--config', self.ovpnconfigpath + '\\' + self.connections[index].name + '.ovpn',
                          '--management', '127.0.0.1', '{0}'.format(port),
                          '--management-query-passwords',
                          '--management-log-cache', '200',
                          '--management-hold'],
                          cwd=self.ovpnconfigpath,
                          startupinfo=startupinfo)
        self.connections[index].sock = ManagementInterfaceHandler(self, '127.0.0.1', port)
        self.connections[index].port = port
        self.setConnState(index, connecting)
        self.updateConnection(index)
        self.updateToolbar(index)

    def ParseLogLine(self, line):
        """Parses and returns log line received from OpenVPN Management Interface."""
        tokens = line.split(',', 2)
        unixtime = tokens[0]
        flags = tokens[1]
        msg = tokens[2]
        time = datetime.fromtimestamp(float(unixtime))
        str_time = time.ctime()
        flags_map = {'I':'INFO', 'F':'FATAL', 'N':'ERROR', 'W':'WARNING', 'D':'DEBUG'}
        str_flags = ''
        if flags in flags_map:
            str_flags = ' ' + flags_map[flags] + ':'
        #return str_time + str_flags + ' ' + msg
        return str_time + ' ' + msg

    def GotLogLine(self, port, line):
        """Called from ManagementInterfaceHandler when new log line is received."""
        #print 'got log line: "{0}"'.format(line)
        index = self.indexFromPort(port)
        parsedline = self.ParseLogLine(line)
        self.connections[index].logbuf.append(parsedline)
        if self.connections[index].logdlg != None:
            self.connections[index].logdlg.AppendText(parsedline)

    def GotStateLine(self, port, line):
        """Called from ManagementInterfaceHandler when new line describing current OpenVPN's state is received."""
        #print 'got state line: "{0}"'.format(line)
        list = line.split(',', 2)
        state = list[1]
        if state == 'CONNECTED':
            index = self.indexFromPort(port)
            self.setConnState(index, connected)
            self.updateConnection(index)
            self.maybeUpdateToolbar(index)

    def OnCmdDisconnect(self, event):
        #print 'OnCmdDisconnect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        self.setConnState(index, disconnecting)
        self.connections[index].sock.send('signal SIGTERM\n')

    # from ManagementInterfaceHandler
    def Disconnected(self, port):
        """Called from ManagementInterfaceHandler when socket to OpenVPN Management Interface is closed."""
        index = self.indexFromPort(port)
        self.setConnState(index, disconnected)
        self.updateConnection(index)
        self.maybeUpdateToolbar(index)

    def OnCmdEditCfg(self, event):
        index = self.list.GetFocusedItem();
        if index != -1:
            subprocess.Popen(['notepad.exe',
                               self.ovpnconfigpath + '\\' + self.connections[index].name + '.ovpn'])

    def OnCmdViewLog(self, event):
        #print 'OnCmdViewLog'
        index = self.list.GetFocusedItem();
        if self.connections[index].logdlg != None: # ?
            return
        logdlg = LogDlg(self, self.connections[index].port, self.connections[index].name)
        self.connections[index].logdlg = logdlg 
        logdlg.Bind(wx.EVT_CLOSE, self.OnLogDlgClose, logdlg)
        for l in self.connections[index].logbuf:
            logdlg.AppendText(l)
        logdlg.Show(True)
        self.updateToolbar(index)

    def OnLogDlgClose(self, event):
        """Called when user closes Log window."""
        #print 'OnLogDlgClose'
        dlg = event.GetEventObject()
        port = dlg.port
        index = self.indexFromPort(port)        
        dlg.Destroy()
        self.connections[index].logdlg = None
        self.updateToolbar(index) 

    def OnCmdRefresh(self, event):
        #print 'OnCmdRefresh'        
        self.updateList()

    def OnCmdAbout(self, event):
        aboutinfo = wx.AboutDialogInfo()
        aboutinfo.SetName('OpenVPN Connection Manager')
        aboutinfo.SetVersion('1.0')
        #aboutinfo.SetDescription('Description')
        #aboutinfo.SetCopyright('(C) 2010')

        # see info about other possible fields here: http://docs.wxwidgets.org/stable/wx_wxaboutdialoginfo.html

        wx.AboutBox(aboutinfo)

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()
