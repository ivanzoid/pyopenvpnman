import wx

class LogDlg(wx.Dialog):
    def __init__(self, parent, port):
        wx.Dialog.__init__(self, parent, -1, 'Log', size=(400,300), style=(wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER))
        
        self.port = port

        self.log = wx.TextCtrl(self, -1, '', style=(wx.TE_RICH2 | wx.TE_MULTILINE
            | wx.TE_READONLY | wx.HSCROLL | wx.TE_BESTWRAP))
        font = wx.Font(face='Courier New', pointSize=8, family=wx.FONTFAMILY_MODERN,
                style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
        defstyle=wx.TextAttr(font=font)
        #defstyle.SetBackgroundColour((0,0,0))

        self.log.SetDefaultStyle(defstyle)

        copy = wx.Button(self, -1, 'Copy all')
        close = wx.Button(self, wx.ID_CLOSE, 'Close')

        self.Bind(wx.EVT_BUTTON, self.OnCopy, copy)
        self.Bind(wx.EVT_BUTTON, self.OnClose, close)

        h1 = wx.BoxSizer(wx.HORIZONTAL)
        h1.AddSpacer(5)
        h1.Add(copy)
        h1.AddSpacer(5)
        h1.Add(close)
        h1.AddSpacer(5)

        v = wx.BoxSizer(wx.VERTICAL)
        v.AddSpacer(5)
        v.Add(self.log, 1, wx.EXPAND)
        v.AddSpacer(5)
        v.Add(h1, 0, wx.ALIGN_CENTER_HORIZONTAL)
        v.AddSpacer(5)

        # sizer only for spacers
        h = wx.BoxSizer(wx.HORIZONTAL)
        h.AddSpacer(7)
        h.Add(v, 1, wx.EXPAND)
        h.AddSpacer(7)

        self.SetSizer(h)
    
    def AppendText(self, text):
        self.log.AppendText(text)

    def OnCopy(self, event):
        self.log.SetSelection(-1, -1) # select all text
        self.log.Copy() # copies to clipboard
        self.log.SetSelection(0, 0) # deselect

    def OnClose(self, event):
        print 'Log:OnClose'        
        self.Close()
