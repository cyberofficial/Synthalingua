Imports System.Net
Imports System.Net.Sockets

Public Class WebBrowserConfig
    Private Sub GenerateLink_Click(sender As Object, e As EventArgs) Handles GenerateLink.Click
        URL_LINK_TXT_BOX.Text = If(RadioLocalHost.Checked, LanIPListBox.Text & ":" & MainUI.PortNumber.Value & "/player.html?", "replace.with.your.own.url:" & MainUI.PortNumber.Value & "/player.html?")
        URL_LINK_TXT_BOX.Text += If(RadioYT.Checked, $"videosource=youtube&id={VideoID.Text}&", "")
        URL_LINK_TXT_BOX.Text += If(RadioTwitch.Checked, $"videosource=twitch&id={VideoID.Text}&", "")
        URL_LINK_TXT_BOX.Text += If(Caption_Orig.Checked, "showoriginal&", "")
        URL_LINK_TXT_BOX.Text += If(Caption_EngTrans.Checked, "showtranslation&", "")
        URL_LINK_TXT_BOX.Text += If(Caption_SecTrans.Checked, "showtranscription&", "")
    End Sub

    Private Sub WebBrowserConfig_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        LanIPListBox.Items.Clear()
        Dim lowestIp As IPAddress = Nothing
        For Each ip In Dns.GetHostEntry(Dns.GetHostName()).AddressList
            If ip.AddressFamily = AddressFamily.InterNetwork Then
                LanIPListBox.Items.Add(ip)
                If lowestIp Is Nothing OrElse lowestIp.ToString().CompareTo(ip.ToString()) > 0 Then
                    lowestIp = ip
                End If
            End If
        Next
        LanIPListBox.Text = lowestIp.ToString()
    End Sub
End Class