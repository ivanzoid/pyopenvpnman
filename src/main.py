import wx
import os
import subprocess
import socket, asyncore, asynchat
import random

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()
id_REFRESH = wx.NewId()

class AuthDlg(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'Authorization required')#, style=(wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER))

        userlabel = wx.StaticText(self, -1, "Username: ")
        passlabel = wx.StaticText(self, -1, "Password: ")

        self.username = wx.TextCtrl(self, -1, "", size=(200,-1))
        self.password = wx.TextCtrl(self, -1, "", size=(200,-1), style=wx.TE_PASSWORD)

        grid = wx.FlexGridSizer(2, 2, vgap=5, hgap=10)

        grid.Add(userlabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.username, 1, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(passlabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.password, 1, wx.ALIGN_CENTER_VERTICAL)

        h2 = self.CreateButtonSizer(wx.OK | wx.CANCEL)

        v = wx.BoxSizer(wx.VERTICAL)
        v.AddSpacer(7)
        v.Add(grid, 0, 0)
        v.AddSpacer(10)
        v.Add(h2, 0, wx.ALIGN_CENTER_HORIZONTAL)
        v.AddSpacer(7)

        # sizer only for spacers
        h = wx.BoxSizer(wx.HORIZONTAL)
        h.AddSpacer(7)
        h.Add(v)
        h.AddSpacer(7)

        self.SetSizer(h)
        h.Fit(self)
        
        self.username.SetFocus()

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
        self.buf = ''

def connStatusString(status):
    if status == 0:
        return 'Disconnected'
    elif status == 1:
        return 'Connected'

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        
        # get list of openvpn connectons
        
        #self.connlist = []
        self.ovpnpath = 'C:\\Program Files\\OpenVPN'
        self.ovpnconfigpath = self.ovpnpath + '\\config'
        self.ovpnexe = self.ovpnpath + '\\bin\\openvpn.exe'
        self.connstatus = {}
        self.connnames = {}
        self.connsocks = {}
        self.connports = {}
        self.logbufs = {}
        
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
        self.imgs.Add(wx.Bitmap('images/notconnected24.png', wx.BITMAP_TYPE_PNG))
        self.imgs.Add(wx.Bitmap('images/connected24.png', wx.BITMAP_TYPE_PNG))
        
        self.list = wx.ListCtrl(self, -1, style=(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES))
        self.list.SetImageList(self.imgs, wx.IMAGE_LIST_SMALL)
        
        self.list.InsertColumn(0, '')
        self.list.InsertColumn(1, 'Name')
        self.list.InsertColumn(2, 'Status')
        
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
        # save statuses of old connections to a dict of pairs name:status
        oldstats = {}
        for i, s in self.connnames.iteritems():
            oldstats[s] = self.connstatus[i]
        
        # get list of current connections
        newlist = self.getConnList(self.ovpnconfigpath)
        self.list.DeleteAllItems()
        for i, s in enumerate(newlist):
            r = random.randint(0, 1)
            if s in oldstats: # check if this connection has saved status
                self.connstatus[i] = oldstats[s]
            else:
                self.connstatus[i] = 0#r
            self.connnames[i] = s
            self.list.InsertStringItem(i, '', imageIndex=self.connstatus[i])
            self.list.SetStringItem(i, col=1, label=s)
            self.list.SetStringItem(i, col=2, label=connStatusString(self.connstatus[i]))
            
    def updateToolbar(self, index):
        if index == -1:
            self.toolbar.EnableTool(id_CONNECT, False)
            self.toolbar.EnableTool(id_DISCONNECT, False)
            self.toolbar.EnableTool(id_EDITCFG, False)
            self.toolbar.EnableTool(id_VIEWLOG, False)
        else: # have selected item
            if self.connstatus[index] == 0: # disconnected
                self.toolbar.EnableTool(id_CONNECT, True)
                self.toolbar.EnableTool(id_DISCONNECT, False)
                self.toolbar.EnableTool(id_EDITCFG, True)
                self.toolbar.EnableTool(id_VIEWLOG, False)
            else:
                self.toolbar.EnableTool(id_CONNECT, False)
                self.toolbar.EnableTool(id_DISCONNECT, True)
                self.toolbar.EnableTool(id_EDITCFG, True)
                self.toolbar.EnableTool(id_VIEWLOG, True)
                
    def updateConnection(self, index):
        if index != -1:
            self.list.SetItemImage(index, self.connstatus[index])
            self.list.SetStringItem(index, col=2, label=connStatusString(self.connstatus[index]))
            
    def OnTimer(self, event):
        asyncore.poll(timeout=0)
        
    def OnConnect(self, event):
        print 'connect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        port = 10598 + index
        subprocess.Popen([self.ovpnexe,
                          '--config', self.ovpnconfigpath + '\\' + self.connnames[index] + '.ovpn',
                          '--management', '127.0.0.1', '{0}'.format(port),
                          '--management-query-passwords',
                          '--management-log-cache', '200',
                          '--management-hold'],
                          cwd=self.ovpnconfigpath)
        self.connsocks[index] = ManagementInterfaceHandler(self, '127.0.0.1', port)
        self.connports[index] = port
        self.connstatus[index] = 1
        self.updateConnection(index)
        self.updateToolbar(index)
        
    def OnDisconnect(self, event):
        print 'disconnect'
        index = self.list.GetFocusedItem()
        if index == -1:
            return
        self.connsocks[index].send('signal SIGTERM\n')
        #self.connstatus[index] = 0
        #self.updateConnection(index)
        #self.updateToolbar(index)
    
    def Disconnected(self, port):
        index = 0
        for i, p in self.connports.iteritems():
            if p == port:
                index = i
                break
        if self.connstatus[index] != 0:
            self.connstatus[index] = 0
            self.updateConnection(index)
            self.updateToolbar(index)

    def OnEditCfg(self, event):
        index = self.list.GetFocusedItem();
        if index != -1:
            subprocess.Popen(['notepad.exe',
                               self.ovpnconfigpath + '\\' + self.connnames[index] + '.ovpn'])
                
    def OnViewLog(self, event):
        print 'view log'        
        
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

