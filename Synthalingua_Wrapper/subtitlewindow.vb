Imports CefSharp.WinForms
Imports CefSharp

Public Class subtitlewindow

    Private WithEvents browser As ChromiumWebBrowser
    Private Sub subtitlewindow_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        ' Set CefSharp settings and cache path
        Dim settings As New CefSettings()
        settings.CachePath = Application.StartupPath & "\Cache"

        ' Add process exe path to sub processes
        settings.BrowserSubprocessPath = Application.StartupPath & "\CefSharp.BrowserSubprocess.exe"

        ' Initialize CefSharp with the settings
        CefSharp.Cef.Initialize(settings)

        ' Create a new browser instance
        browser = New ChromiumWebBrowser("http://example.com")

        ' Dock the browser in the main form
        browser.Dock = DockStyle.Fill
        Me.Controls.Add(browser)
    End Sub

    Private Sub subtitlewindow_FormClosing(sender As Object, e As FormClosingEventArgs) Handles MyBase.FormClosing
        browser.Dispose()
        CefSharp.Cef.Shutdown()
        Cef.Shutdown()
    End Sub
End Class