Public Class WebBrowserConfig
    Private Sub GenerateLink_Click(sender As Object, e As EventArgs) Handles GenerateLink.Click
        If RadioLocalHost.Checked = True Then
            URL_LINK_TXT_BOX.Text = "localhost:" & MainUI.PortNumber.Value & "/player.html?"
        End If
        If RadioShare.Checked = True Then
            URL_LINK_TXT_BOX.Text = "replace.with.your.own.url:" & MainUI.PortNumber.Value & "/player.html?"
        End If
        If RadioYT.Checked = True Then
            URL_LINK_TXT_BOX.Text += $"videosource=youtube&id={VideoID.Text}&"
        End If
        If RadioTwitch.Checked = True Then
            URL_LINK_TXT_BOX.Text += $"videosource=twitch&id={VideoID.Text}&"
        End If
        If Caption_Orig.Checked = True Then
            URL_LINK_TXT_BOX.Text += "showoriginal&"
        End If
        If Caption_EngTrans.Checked = True Then
            URL_LINK_TXT_BOX.Text += "showtranslation&"
        End If
        If Caption_SecTrans.Checked = True Then
            URL_LINK_TXT_BOX.Text += "showtranscription&"
        End If

    End Sub
End Class