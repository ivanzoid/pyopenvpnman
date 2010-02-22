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
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_TEXT | wx.TB_NO_TOOLTIPS )

        self.toolbar.AddLabelTool(id_CONNECT, 'Connect', wx.Bitmap('images/connect.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_DISCONNECT, 'Disconnect', wx.Bitmap('images/disconnect.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_EDITCFG, 'Edit config', wx.Bitmap('images/editcfg.png', wx.BITMAP_TYPE_PNG))
        self.toolbar.AddLabelTool(id_VIEWLOG, 'View log', wx.Bitmap('images/viewlog.png', wx.BITMAP_TYPE_PNG))
        
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
        
#        self.list.InsertImageItem(index=0, imageIndex=0)
#        self.list.InsertImageItem(index=1, imageIndex=1)
#        self.list.InsertImageItem(index=2, imageIndex=0)
        
#        self.list.InsertImageStringItem(index=0, label='', imageIndex=0)
#        self.list.InsertImageStringItem(index=0, label='', imageIndex=0)
#        self.list.InsertImageStringItem(index=0, label='', imageIndex=0)
        
        self.list.InsertStringItem(0, '')
        self.list.InsertStringItem(1, '')
        #self.list.InsertStringItem(2, '')
        
        for i in range(len(self.ovpnnames)):
            #self.list.SetStringItem(index=i, col=0, label='', imageId=1)
            #self.list.SetItemImage(i, 0)
            self.list.SetStringItem(index=i, col=0, imageId=1, label='')
            self.list.SetStringItem(index=i, col=1, label=self.ovpnnames[i])
            self.list.SetStringItem(index=i, col=2, label='Disconnected')            
            #self.list.SetStringItem(index=i, col=2, label='Disconnected')
            
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        
    def getConnList(self):
        files = os.listdir('C:\\Program Files\\OpenVPN\\config')
        ovpnfiles = filter(lambda s: s.endswith('.ovpn'), files)
        self.ovpnnames = map(lambda s: s[:-5], ovpnfiles)
        
        print self.ovpnnames
                

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "OpenVPN Connection Manager")
        wnd.Show(True)
        #self.SetTopWindow(wnd)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

