import wx
import os
import random

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()
id_REFRESH = wx.NewId()

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
        self.ovpnpath = 'C:\\Program Files\\OpenVPN\\config'
        self.connstatus = {}
        self.connnames = {}
        
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
        
        self.list.Select(0) # select first item
        
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
        newlist = self.getConnList(self.ovpnpath)
        self.list.DeleteAllItems()
        for i, s in enumerate(newlist):
            r = random.randint(0, 1)
            if s in oldstats: # check if this connection has saved status
                self.connstatus[i] = oldstats[s]
            else:
                self.connstatus[i] = r
            self.connnames[i] = s
            self.list.InsertStringItem(i, '', imageIndex=self.connstatus[i])
            self.list.SetStringItem(i, col=1, label=s)
            self.list.SetStringItem(i, col=2, label=connStatusString(self.connstatus[i]))
        
    def OnConnect(self, event):
        print 'connect'
        
    def OnDisconnect(self, event):
        print 'disconnect'        

    def OnEditCfg(self, event):
        print 'edit cfg'
                
    def OnViewLog(self, event):
        print 'view log'        
        
    def OnRefresh(self, event):
        self.updateList()
        print 'refresh'
        
    def OnItemSelected(self, event):
        index = event.m_itemIndex
        if self.connstatus[index] == 0: # disconnected
            self.toolbar.EnableTool(id_CONNECT, True)
            self.toolbar.EnableTool(id_DISCONNECT, False)
            self.toolbar.EnableTool(id_VIEWLOG, False)
        else:
            self.toolbar.EnableTool(id_CONNECT, False)
            self.toolbar.EnableTool(id_DISCONNECT, True)
            self.toolbar.EnableTool(id_VIEWLOG, True)
    
    def OnItemDeselected(self, event):
        if self.list.GetSelectedItemCount() == 0:
            self.toolbar.EnableTool(id_CONNECT, False)
            self.toolbar.EnableTool(id_DISCONNECT, False)
            self.toolbar.EnableTool(id_EDITCFG, False)
            self.toolbar.EnableTool(id_VIEWLOG, False)

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

