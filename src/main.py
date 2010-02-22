import wx
import os

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()
id_REFRESH = wx.NewId()

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        
        # get list of openvpn connectons
        
        self.connlist = []
        self.ovpnpath = 'C:\\Program Files\\OpenVPN\\config'
        
        # init toolbar
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_TEXT | wx.TB_NO_TOOLTIPS )

        self.toolbar.AddLabelTool(id_CONNECT, 'Connect', wx.Bitmap('images/connect.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_DISCONNECT, 'Disconnect', wx.Bitmap('images/disconnect.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_EDITCFG, 'Edit config', wx.Bitmap('images/editcfg.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_VIEWLOG, 'View log', wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG))
        refresh = self.toolbar.AddLabelTool(id_REFRESH, 'Refresh', wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_TOOL, self.OnRefresh, refresh, id_REFRESH)
        
        self.toolbar.Realize()
        
        # init list view

        self.imgs = wx.ImageList(24, 24, mask=True)
        self.imgs.Add(wx.Bitmap('images/connected24.png', wx.BITMAP_TYPE_PNG))
        self.imgs.Add(wx.Bitmap('images/notconnected24.png', wx.BITMAP_TYPE_PNG))
        
        self.list = wx.ListCtrl(self, -1, style=(wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES))
        self.list.SetImageList(self.imgs, wx.IMAGE_LIST_SMALL)
        
        self.list.InsertColumn(0, '')
        self.list.InsertColumn(1, 'Name')
        self.list.InsertColumn(2, 'Status')
        
        self.updateList()            
            
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        
    def getConnList(self, path):
        files = os.listdir(path)
        ovpnfiles = filter(lambda s: s.endswith('.ovpn'), files)
        ovpnnames = map(lambda s: s[:-5], ovpnfiles)
        return ovpnnames
        
    def updateList(self):
        newlist = self.getConnList(self.ovpnpath)
        self.list.DeleteAllItems()
        for c in newlist:
            item = wx.ListItem()
            item.SetImage(1)
            i = self.list.InsertItem(item)
            self.list.SetStringItem(i, col=1, label=c)
            self.list.SetStringItem(i, col=2, label='Disconnected')
        self.connlist = newlist
        
    def OnRefresh(self, event):
        self.updateList()            


class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        #self.SetTopWindow(wnd)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

