import wx
import os
import subprocess
import socket, asyncore, asynchat

from authdlg import *
from logdlg import *

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()
id_REFRESH = wx.NewId()

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
        print 'handle_connect ({0})'.format(self.port)
        asynchat.async_chat.handle_connect(self)
        
    def handle_close(self):
        print 'handle_close'
        self.mainwnd.Disconnected(self.port)
        asynchat.async_chat.handle_close(self)
    
    def collect_incoming_data(self, data):
        #print 'collect_incoming_data ({0}) data: "{1}"'.format(self.port, data)
        self.buf += data
        
    def found_terminator(self):
        print 'found_terminator ({0}) buf: "{1}"'.format(self.port, self.buf)
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
(initial_disconnected, disconnected, failed, connecting, connected) = range(5)

class Connection(object):
    def __init__(self, name):
        self.name = name
        self.state = initial_disconnected # do not set this field directly, use MainWindow.setConnState()
        self.sock = None # ManagementInterfaceHandler
        self.port = 0
        self.logbuf = []
        self.logdlg = None # LogDlg
    def stateString(self):
        if self.state == initial_disconnected or self.state == disconnected:
            return 'Disconnected'
        elif self.state == failed:
            return 'Error'
        elif self.state == connecting:
            return 'Connecting'
        elif self.state == connected:
            return 'Connected'
        else:
            return 'Error'

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(400,300))
        
        self.ovpnpath = 'C:\\Program Files\\OpenVPN'
        self.ovpnconfigpath = self.ovpnpath + '\\config'
        self.ovpnexe = self.ovpnpath + '\\bin\\openvpn.exe'
        self.traymsg = 'OpenVPN Connection Manager'
        self.connections = {}
        
        # init tray icon
        
        self.notconnectedIcon = wx.Icon('images/fail32.ico', wx.BITMAP_TYPE_ICO)
        self.connectingIcon = wx.Icon('images/waiting32.ico', wx.BITMAP_TYPE_ICO)
        self.connectedIcon = wx.Icon('images/ack32.ico', wx.BITMAP_TYPE_ICO)
        
        self.trayicon = wx.TaskBarIcon()
        self.trayicon.SetIcon(self.notconnectedIcon, self.traymsg)
        
        self.wndshown = True
        
        self.Bind(wx.EVT_ICONIZE, self.OnIconize)
        self.trayicon.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTrayIconClick)
        
        # init toolbar
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_TEXT | wx.TB_NO_TOOLTIPS )

        connect = self.toolbar.AddLabelTool(id_CONNECT, 'Connect', wx.Bitmap('images/connect.png', wx.BITMAP_TYPE_PNG))
        disconnect = self.toolbar.AddLabelTool(id_DISCONNECT, 'Disconnect', wx.Bitmap('images/disconnect.png', wx.BITMAP_TYPE_PNG))
        editcfg = self.toolbar.AddLabelTool(id_EDITCFG, 'Edit config', wx.Bitmap('images/editcfg.png', wx.BITMAP_TYPE_PNG))
        viewlog = self.toolbar.AddLabelTool(id_VIEWLOG, 'View log', wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG))
        refresh = self.toolbar.AddLabelTool(id_REFRESH, 'Refresh', wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_TOOL, self.OnConnect, connect, id_CONNECT)
        self.Bind(wx.EVT_TOOL, self.OnDisconnect, disconnect, id_DISCONNECT)
        self.Bind(wx.EVT_TOOL, self.OnEditCfg, editcfg, id_EDITCFG)
        self.Bind(wx.EVT_TOOL, self.OnViewLog, viewlog, id_VIEWLOG)
        self.Bind(wx.EVT_TOOL, self.OnRefresh, refresh, id_REFRESH)
        
        self.toolbar.Realize()
        
        self.toolbar.EnableTool(id_CONNECT, False)
        self.toolbar.EnableTool(id_DISCONNECT, False)
        self.toolbar.EnableTool(id_EDITCFG, False)
        self.toolbar.EnableTool(id_VIEWLOG, False)
        
        # init list view

        self.imgs = wx.ImageList(24, 24, mask=True)
        self.disconnectedImgId = self.imgs.Add(wx.Bitmap('images/notconnected24.png', wx.BITMAP_TYPE_PNG))
        self.connectedImgId = self.imgs.Add(wx.Bitmap('images/connected24.png', wx.BITMAP_TYPE_PNG))
        self.connectingImgId = self.imgs.Add(wx.Bitmap('images/connecting24.png', wx.BITMAP_TYPE_PNG))

        self.list = wx.ListCtrl(self, -1, style=(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES))
        self.list.SetImageList(self.imgs, wx.IMAGE_LIST_SMALL)
        
        self.list.InsertColumn(0, '')
        self.list.InsertColumn(1, 'Name')
        self.list.InsertColumn(2, 'state')
        
        self.updateList()
            
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
        
        self.list.Focus(0)
        self.list.Select(0)
        
        # create timer which will poll incoming data from sockets to 
        # our ManagementInterfaceHandler
        self.timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(20, wx.TIMER_CONTINUOUS)
        
    def getConnList(self, path):
        files = os.listdir(path)
        ovpnfiles = filter(lambda s: s.endswith('.ovpn'), files)
        ovpnnames = map(lambda s: s[:-5], ovpnfiles)
        return ovpnnames
        
    def updateList(self):
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
            self.list.InsertStringItem(i, '', self.imgIndexBystate(self.connections[i].state))
            self.list.SetStringItem(i, 1, s)
            self.list.SetStringItem(i, 2, self.connections[i].stateString())
    
    def trayIconByState(self, state):
        if state == connecting:
            return self.connectingIcon
        elif state == connected:
            return self.connectedIcon
        else:
            return self.notconnectedIcon
    
    def updateTrayIcon(self):
        maxstate = disconnected
        for c in self.connections.itervalues():
            if c.state > maxstate:
                maxstate = c.state
        self.trayicon.SetIcon(self.trayIconByState(maxstate), self.traymsg)
            
    def setConnState(self, index, state):
        self.connections[index].state = state
        if state == connected:
            self.trayicon.SetIcon(self.trayIconByState(state), self.traymsg)
        else:
            self.updateTrayIcon()
            
    def imgIndexBystate(self, state):
        if state == initial_disconnected or state == disconnected or state == failed:
            return self.disconnectedImgId
        elif state == connecting:
            return self.connectingImgId
        elif state == connected:
            return self.connectedImgId
        else: # ?
            return -1
            
    def updateToolbar(self, index):
        if index == -1:
            self.toolbar.EnableTool(id_CONNECT, False)
            self.toolbar.EnableTool(id_DISCONNECT, False)
            self.toolbar.EnableTool(id_EDITCFG, False)
            self.toolbar.EnableTool(id_VIEWLOG, False)
        else: # have selected item
            self.toolbar.EnableTool(id_EDITCFG, True)            
            if self.connections[index].state == disconnected \
            or self.connections[index].state == initial_disconnected \
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
        curindex = self.list.GetFocusedItem()
        if curindex == index:
            self.updateToolbar(index)
                
    def updateConnection(self, index):
        if index != -1:
            self.list.SetItemImage(index, self.imgIndexBystate(self.connections[index].state))
            self.list.SetStringItem(index, 2, self.connections[index].stateString())
    
    def indexFromPort(self, port):
        for i, c in self.connections.iteritems():
            if c.port == port:
                return i
        return -1
    
    def OnIconize(self, event):
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
            
    def OnTimer(self, event):
        asyncore.poll(timeout=0)
        
    def OnConnect(self, event):
        print 'connect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        port = 10598 + index
        subprocess.Popen([self.ovpnexe,
                          '--config', self.ovpnconfigpath + '\\' + self.connections[index].name + '.ovpn',
                          '--management', '127.0.0.1', '{0}'.format(port),
                          '--management-query-passwords',
                          '--management-log-cache', '200',
                          '--management-hold'],
                          cwd=self.ovpnconfigpath)
        self.connections[index].sock = ManagementInterfaceHandler(self, '127.0.0.1', port)
        self.connections[index].port = port
        self.setConnState(index, connecting)
        self.updateConnection(index)
        self.updateToolbar(index)
        
    def OnDisconnect(self, event):
        print 'disconnect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        self.connections[index].sock.send('signal SIGTERM\n')

    # from ManagementInterfaceHandler
    def Disconnected(self, port):
        index = self.indexFromPort(port)
        self.setConnState(index, disconnected)
        self.updateConnection(index)
        self.maybeUpdateToolbar(index)
            
    def GotLogLine(self, port, line):
        print 'got log line: "{0}"'.format(line)
        index = self.indexFromPort(port)        
        self.connections[index].logbuf.append(line)
        if self.connections[index].logdlg != None:
            self.connections[index].logdlg.AppendText(line)
            
    def GotStateLine(self, port, line):
        print 'got state line: "{0}"'.format(line)
        list = line.split(',', 2)
        state = list[1]
        print 'state:' + state
        if state == 'CONNECTED':
            index = self.indexFromPort(port)
            print 'index: ' + str(index)
            self.setConnState(index, connected)
            self.updateConnection(index)
            self.maybeUpdateToolbar(index)

    def OnEditCfg(self, event):
        index = self.list.GetFocusedItem();
        if index != -1:
            subprocess.Popen(['notepad.exe',
                               self.ovpnconfigpath + '\\' + self.connnames[index] + '.ovpn'])
                
    def OnViewLog(self, event):
        print 'view log'
        index = self.list.GetFocusedItem();
        if self.connections[index].logdlg != None: # ?
            return
        logdlg = LogDlg(self, self.connections[index].port)
        self.connections[index].logdlg = logdlg 
        logdlg.Bind(wx.EVT_CLOSE, self.OnLogDlgClose, logdlg)
        for l in self.connections[index].logbuf:
            logdlg.AppendText(l)
        logdlg.Show(True)
        self.updateToolbar(index)
        
    def OnLogDlgClose(self, event):
        print 'OnLogDlgClose'
        dlg = event.GetEventObject()
        port = dlg.port
        index = self.indexFromPort(port)        
        dlg.Destroy()
        self.connections[index].logdlg = None
        self.updateToolbar(index) 
        
    def OnRefresh(self, event):
        self.updateList()
        print 'refresh'
        
    def OnItemSelected(self, event):
        self.updateToolbar(event.m_itemIndex)
    
    def OnItemDeselected(self, event):
        if self.list.GetSelectedItemCount() == 0:
            self.updateToolbar(-1)

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

