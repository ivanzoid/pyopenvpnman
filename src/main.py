import wx
import os

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        
        # get list of openvpn connectons
        
        self.getConnList()
        
        # init toolbar
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        self.toolbar.AddSimpleTool(
            id_CONNECT, wx.Bitmap('images/connect.png', wx.BITMAP_TYPE_PNG), 'Connect')
        self.toolbar.AddSimpleTool(
            id_DISCONNECT, wx.Bitmap('images/disconnect.png', wx.BITMAP_TYPE_PNG), 'Disconnect')
        self.toolbar.AddSimpleTool(
            id_EDITCFG, wx.Bitmap('images/editcfg.png', wx.BITMAP_TYPE_PNG), 'Edit config')
        self.toolbar.AddSimpleTool(
            id_VIEWLOG, wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG), 'View log')
        
        self.toolbar.Realize()
        
        # init list view
        
        self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
        
        self.list.InsertColumn(0, '') # image
        self.list.InsertColumn(1, 'Connection')
        self.list.InsertColumn(2, 'Status')
        
        self.list.InsertStringItem(0, 'Item 1')
        self.list.InsertStringItem(1, 'Item 2')
        self.list.InsertStringItem(2, 'Item 3')
        
        for i in range(len(self.ovpnnames)):
            self.list.SetStringItem(i, 1, self.ovpnnames[i])
            self.list.SetStringItem(i, 2, 'Disconnected')
        
    def getConnList(self):
        files = os.listdir('C:\\Program Files\\OpenVPN\\config')
        ovpnfiles = filter(lambda s: s.endswith('.ovpn'), files)
        self.ovpnnames = map(lambda s: s[:-5], ovpnfiles)
        
        print self.ovpnnames
                

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        self.SetTopWindow(wnd)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

