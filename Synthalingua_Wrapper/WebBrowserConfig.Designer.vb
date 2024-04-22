<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class WebBrowserConfig
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Label1 = New Label()
        GroupBox1 = New GroupBox()
        RadioShare = New RadioButton()
        RadioLocalHost = New RadioButton()
        GroupBox2 = New GroupBox()
        RadioTwitch = New RadioButton()
        RadioYT = New RadioButton()
        GroupBox3 = New GroupBox()
        Label2 = New Label()
        VideoID = New TextBox()
        GroupBox4 = New GroupBox()
        Caption_SecTrans = New CheckBox()
        Caption_EngTrans = New CheckBox()
        Caption_Orig = New CheckBox()
        GenerateLink = New Button()
        URL_LINK_TXT_BOX = New TextBox()
        Label3 = New Label()
        GroupBox1.SuspendLayout()
        GroupBox2.SuspendLayout()
        GroupBox3.SuspendLayout()
        GroupBox4.SuspendLayout()
        SuspendLayout()
        ' 
        ' Label1
        ' 
        Label1.AutoSize = True
        Label1.Font = New Font("Segoe UI", 16F)
        Label1.Location = New Point(13, 9)
        Label1.Margin = New Padding(4, 0, 4, 0)
        Label1.Name = "Label1"
        Label1.Size = New Size(644, 90)
        Label1.TabIndex = 0
        Label1.Text = "Customize The Web Player for the Web browser." & vbCrLf & "You can then share this with others if you have port forwarding or" & vbCrLf & "you can use for your self."
        ' 
        ' GroupBox1
        ' 
        GroupBox1.Controls.Add(RadioShare)
        GroupBox1.Controls.Add(RadioLocalHost)
        GroupBox1.Font = New Font("Segoe UI", 13F)
        GroupBox1.Location = New Point(13, 104)
        GroupBox1.Margin = New Padding(4, 5, 4, 5)
        GroupBox1.Name = "GroupBox1"
        GroupBox1.Padding = New Padding(4, 5, 4, 5)
        GroupBox1.Size = New Size(257, 111)
        GroupBox1.TabIndex = 1
        GroupBox1.TabStop = False
        GroupBox1.Text = "(1) I am using this for:"
        ' 
        ' RadioShare
        ' 
        RadioShare.AutoSize = True
        RadioShare.Location = New Point(8, 67)
        RadioShare.Margin = New Padding(4, 5, 4, 5)
        RadioShare.Name = "RadioShare"
        RadioShare.Size = New Size(167, 29)
        RadioShare.TabIndex = 1
        RadioShare.Text = "Share with others"
        RadioShare.UseVisualStyleBackColor = True
        ' 
        ' RadioLocalHost
        ' 
        RadioLocalHost.AutoSize = True
        RadioLocalHost.Checked = True
        RadioLocalHost.Location = New Point(8, 34)
        RadioLocalHost.Margin = New Padding(4, 5, 4, 5)
        RadioLocalHost.Name = "RadioLocalHost"
        RadioLocalHost.Size = New Size(89, 29)
        RadioLocalHost.TabIndex = 0
        RadioLocalHost.TabStop = True
        RadioLocalHost.Text = "My Self"
        RadioLocalHost.UseVisualStyleBackColor = True
        ' 
        ' GroupBox2
        ' 
        GroupBox2.Controls.Add(RadioTwitch)
        GroupBox2.Controls.Add(RadioYT)
        GroupBox2.Location = New Point(278, 104)
        GroupBox2.Margin = New Padding(4, 5, 4, 5)
        GroupBox2.Name = "GroupBox2"
        GroupBox2.Padding = New Padding(4, 5, 4, 5)
        GroupBox2.Size = New Size(150, 111)
        GroupBox2.TabIndex = 2
        GroupBox2.TabStop = False
        GroupBox2.Text = "(2) Video Source is:"
        ' 
        ' RadioTwitch
        ' 
        RadioTwitch.AutoSize = True
        RadioTwitch.Location = New Point(7, 67)
        RadioTwitch.Name = "RadioTwitch"
        RadioTwitch.Size = New Size(79, 29)
        RadioTwitch.TabIndex = 1
        RadioTwitch.Text = "Twitch"
        RadioTwitch.UseVisualStyleBackColor = True
        ' 
        ' RadioYT
        ' 
        RadioYT.AutoSize = True
        RadioYT.Checked = True
        RadioYT.Location = New Point(7, 32)
        RadioYT.Name = "RadioYT"
        RadioYT.Size = New Size(98, 29)
        RadioYT.TabIndex = 0
        RadioYT.TabStop = True
        RadioYT.Text = "YouTube"
        RadioYT.UseVisualStyleBackColor = True
        ' 
        ' GroupBox3
        ' 
        GroupBox3.Controls.Add(Label2)
        GroupBox3.Controls.Add(VideoID)
        GroupBox3.Location = New Point(435, 104)
        GroupBox3.Name = "GroupBox3"
        GroupBox3.Size = New Size(296, 151)
        GroupBox3.TabIndex = 3
        GroupBox3.TabStop = False
        GroupBox3.Text = "(3) Video ID:"
        ' 
        ' Label2
        ' 
        Label2.AutoSize = True
        Label2.Location = New Point(6, 67)
        Label2.Name = "Label2"
        Label2.Size = New Size(282, 75)
        Label2.TabIndex = 1
        Label2.Text = "Provide a Video ID:" & vbCrLf & "Example for Twitch: streamername" & vbCrLf & "YouTube: qWNQUvIk954"
        ' 
        ' VideoID
        ' 
        VideoID.Location = New Point(6, 30)
        VideoID.Name = "VideoID"
        VideoID.Size = New Size(282, 31)
        VideoID.TabIndex = 0
        ' 
        ' GroupBox4
        ' 
        GroupBox4.Controls.Add(Caption_SecTrans)
        GroupBox4.Controls.Add(Caption_EngTrans)
        GroupBox4.Controls.Add(Caption_Orig)
        GroupBox4.Location = New Point(13, 223)
        GroupBox4.Name = "GroupBox4"
        GroupBox4.Size = New Size(257, 144)
        GroupBox4.TabIndex = 4
        GroupBox4.TabStop = False
        GroupBox4.Text = "(4) Captions Type"
        ' 
        ' Caption_SecTrans
        ' 
        Caption_SecTrans.AutoSize = True
        Caption_SecTrans.Location = New Point(8, 100)
        Caption_SecTrans.Name = "Caption_SecTrans"
        Caption_SecTrans.Size = New Size(203, 29)
        Caption_SecTrans.TabIndex = 2
        Caption_SecTrans.Text = "Secondary Translation"
        Caption_SecTrans.UseVisualStyleBackColor = True
        ' 
        ' Caption_EngTrans
        ' 
        Caption_EngTrans.AutoSize = True
        Caption_EngTrans.Location = New Point(8, 65)
        Caption_EngTrans.Name = "Caption_EngTrans"
        Caption_EngTrans.Size = New Size(176, 29)
        Caption_EngTrans.TabIndex = 1
        Caption_EngTrans.Text = "English Translation"
        Caption_EngTrans.UseVisualStyleBackColor = True
        ' 
        ' Caption_Orig
        ' 
        Caption_Orig.AutoSize = True
        Caption_Orig.Location = New Point(8, 30)
        Caption_Orig.Name = "Caption_Orig"
        Caption_Orig.Size = New Size(93, 29)
        Caption_Orig.TabIndex = 0
        Caption_Orig.Text = "Original"
        Caption_Orig.UseVisualStyleBackColor = True
        ' 
        ' GenerateLink
        ' 
        GenerateLink.Location = New Point(13, 373)
        GenerateLink.Name = "GenerateLink"
        GenerateLink.Size = New Size(185, 40)
        GenerateLink.TabIndex = 5
        GenerateLink.Text = "(5) Generate Link"
        GenerateLink.UseVisualStyleBackColor = True
        ' 
        ' URL_LINK_TXT_BOX
        ' 
        URL_LINK_TXT_BOX.Location = New Point(13, 419)
        URL_LINK_TXT_BOX.Name = "URL_LINK_TXT_BOX"
        URL_LINK_TXT_BOX.Size = New Size(718, 31)
        URL_LINK_TXT_BOX.TabIndex = 6
        ' 
        ' Label3
        ' 
        Label3.AutoSize = True
        Label3.Location = New Point(285, 267)
        Label3.Name = "Label3"
        Label3.Size = New Size(449, 100)
        Label3.TabIndex = 7
        Label3.Text = "⚠️ When sharing with twitch with others, the domain" & vbCrLf & "name must use HTTPS It also must not be a ip address." & vbCrLf & vbCrLf & "This is Twitch's ruling, not mine."
        ' 
        ' WebBrowserConfig
        ' 
        AutoScaleDimensions = New SizeF(9F, 23F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(746, 468)
        Controls.Add(Label3)
        Controls.Add(URL_LINK_TXT_BOX)
        Controls.Add(GenerateLink)
        Controls.Add(GroupBox4)
        Controls.Add(GroupBox3)
        Controls.Add(GroupBox2)
        Controls.Add(GroupBox1)
        Controls.Add(Label1)
        Font = New Font("Segoe UI", 13F)
        FormBorderStyle = FormBorderStyle.Fixed3D
        Margin = New Padding(4, 5, 4, 5)
        MaximizeBox = False
        Name = "WebBrowserConfig"
        StartPosition = FormStartPosition.CenterParent
        Text = "Web Browser Config"
        GroupBox1.ResumeLayout(False)
        GroupBox1.PerformLayout()
        GroupBox2.ResumeLayout(False)
        GroupBox2.PerformLayout()
        GroupBox3.ResumeLayout(False)
        GroupBox3.PerformLayout()
        GroupBox4.ResumeLayout(False)
        GroupBox4.PerformLayout()
        ResumeLayout(False)
        PerformLayout()
    End Sub

    Friend WithEvents Label1 As Label
    Friend WithEvents GroupBox1 As GroupBox
    Friend WithEvents RadioShare As RadioButton
    Friend WithEvents RadioLocalHost As RadioButton
    Friend WithEvents GroupBox2 As GroupBox
    Friend WithEvents RadioTwitch As RadioButton
    Friend WithEvents RadioYT As RadioButton
    Friend WithEvents GroupBox3 As GroupBox
    Friend WithEvents Label2 As Label
    Friend WithEvents VideoID As TextBox
    Friend WithEvents GroupBox4 As GroupBox
    Friend WithEvents Caption_Orig As CheckBox
    Friend WithEvents Caption_SecTrans As CheckBox
    Friend WithEvents Caption_EngTrans As CheckBox
    Friend WithEvents GenerateLink As Button
    Friend WithEvents URL_LINK_TXT_BOX As TextBox
    Friend WithEvents Label3 As Label
End Class
