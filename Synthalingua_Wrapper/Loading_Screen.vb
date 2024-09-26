Public NotInheritable Class Loading_Screen
    Private Sub Loading_Screen_Load(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Load

        If My.Application.Info.Title <> "" Then
            ApplicationTitle.Text = My.Application.Info.Title
        Else
            ApplicationTitle.Text = System.IO.Path.GetFileNameWithoutExtension(My.Application.Info.AssemblyName)
        End If
        Version.Text = My.Application.Info.Version.ToString
        Copyright.Text = My.Application.Info.Copyright
    End Sub

    Private Sub ApplicationTitle_Click(sender As Object, e As EventArgs) Handles ApplicationTitle.Click

    End Sub
End Class
