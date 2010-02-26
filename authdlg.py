import wx

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
