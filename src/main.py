import wx

id_CONNECT = wx.NewId()
id_DISCONNECT = wx.NewId()
id_EDITCFG = wx.NewId()
id_VIEWLOG = wx.NewId()

class MainWindow(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)

        # init toolbar
        #tsize = (15,15)
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        #artBmp = wx.ArtProvider.GetBitmap
        
        self.toolbar.AddSimpleTool(
            id_CONNECT, wx.Bitmap('images/connect.bmp', wx.BITMAP_TYPE_BMP), 'Connect')
        self.toolbar.AddSimpleTool(
            id_DISCONNECT, wx.Bitmap('images/disconnect.bmp', wx.BITMAP_TYPE_BMP), 'Disconnect')
        self.toolbar.AddSimpleTool(
            id_EDITCFG, wx.Bitmap('images/editcfg.bmp', wx.BITMAP_TYPE_BMP), 'Edit config')
        self.toolbar.AddSimpleTool(
            id_VIEWLOG, wx.Bitmap('images/viewlog.bmp', wx.BITMAP_TYPE_BMP), 'View log')
        
        self.toolbar.Realize()


    # This method is called by the System when the window is resized,
    # because of the association above.
    def OnSize(self, event):
        size = event.GetSize()
        self.sizeCtrl.SetValue("%s, %s" % (size.width, size.height))

        # tell the event system to continue looking for an event handler,
        # so the default handler will get called.
        event.Skip()

    # This method is called by the System when the window is moved,
    # because of the association above.
    def OnMove(self, event):
        pos = event.GetPosition()
        self.posCtrl.SetValue("%s, %s" % (pos.x, pos.y))

class App(wx.App):
    def OnInit(self):
        wnd = MainWindow(None, -1, "This is a test")
        wnd.Show(True)
        self.SetTopWindow(wnd)
        return True

if __name__ == '__main__':
    app = App(0)
    app.MainLoop()

