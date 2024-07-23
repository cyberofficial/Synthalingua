Imports System.IO
Imports System.Net.Http
Imports System.Net.Sockets
Imports System.Runtime.InteropServices
Imports System.Security.Cryptography.X509Certificates
Imports System.Text
Imports System.Text.RegularExpressions
Imports System.Threading


Public Class subtitlewindow
    Private httpClient As HttpClient
    Private cts As CancellationTokenSource

    ' Declare variables for URLs
    Private URLHeader As String
    Private URLTranslatedHeader As String
    Private URLTranscribedHeader As String

    Private iOriginalText As Boolean = False
    Private iTranscribeText As Boolean = False
    Private iTranslateText As Boolean = False

    Dim RTL_Mode As Boolean = False
    Dim Main_BG_COLOR As System.Drawing.Color = Color.FromArgb(0, 177, 64)

    Dim resizing As Boolean = False
    Dim resizableCorner As String = ""
    Dim startPoint As Point
    Dim startSize As Size
    Dim startLocation As Point
    Dim endPoint As Point

    Dim Dragable As Boolean = False

    ' P/Invoke declarations
    <DllImport("user32.dll")>
    Public Shared Function SendMessage(hWnd As IntPtr, Msg As Integer, wParam As Integer, lParam As Integer) As Integer
    End Function

    <DllImport("user32.dll")>
    Public Shared Function ReleaseCapture() As Boolean
    End Function

    Public Sub New()
        Dim CaptionsHost As String = "localhost"
        ' This call is required by the designer.
        InitializeComponent()

        ' Initialize HttpClient and CancellationTokenSource
        httpClient = New HttpClient()
        cts = New CancellationTokenSource()

        ' Set the port number from MainUI and initialize URLs
        Dim SubPortNumber As String = MainUI.PortNumber.Value.ToString()
        URLHeader = $"http://{CaptionsHost}:{SubPortNumber}/update-header"
        URLTranslatedHeader = $"http://{CaptionsHost}:{SubPortNumber}/update-translated-header"
        URLTranscribedHeader = $"http://{CaptionsHost}:{SubPortNumber}/update-transcribed-header"

        ' Initialize label properties for auto-wrapping
        InitializeLabelWrapping(headertextlbl)
        'InitializeLabelWrapping(translatedheaderlbl)
        'InitializeLabelWrapping(transcribedheaderlbl)
    End Sub

    Private Sub InitializeLabelWrapping(label As Label)
        'label.AutoSize = True
        label.AutoEllipsis = True
        label.MaximumSize = New Size(ClientSize.Width, 0)
    End Sub

    Private Function CountBlacklistedPhrases() As Integer
        Dim numberOfPhrases As Integer = 0

        Try
            ' Read blacklisted phrases from file
            Dim lines As String() = File.ReadAllLines(MainUI.WordBlockListLocation.ToString)

            ' Count the number of loaded phrases
            numberOfPhrases = lines.Length
        Catch ex As Exception
            Debug.WriteLine("Error counting blacklisted phrases: " & ex.Message)
        End Try

        Return numberOfPhrases
    End Function

    Private Sub subtitlewindow_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        InfoSaverTimer.Interval = 25 ' Set timer interval to 25ms
        InfoSaverTimer.Start()

        Dim numberOfPhrases As Integer = CountBlacklistedPhrases()

        ' Set the form title with the number of loaded phrases
        'If MainUI.WordBlockList.Checked = True Then
        '   Me.Text = $"Subtitle Window | Loaded {numberOfPhrases} phrases from word list."
        'End If



        With headertextlbl
            .Font = My.Settings.headertextlbl_font
            .ForeColor = My.Settings.headertextlbl_forecolor
            .BackColor = My.Settings.headertextlbl_backcolor
        End With
        'With translatedheaderlbl
        '    .Font = My.Settings.headertextlbl_font
        '    .ForeColor = My.Settings.headertextlbl_forecolor
        '    .BackColor = My.Settings.headertextlbl_backcolor
        'End With
        'With transcribedheaderlbl
        '    .Font = My.Settings.headertextlbl_font
        '    .ForeColor = My.Settings.headertextlbl_forecolor
        '    .BackColor = My.Settings.headertextlbl_backcolor
        'End With

        If My.Settings.subwindow_lmode = True Then
            headertextlbl.RightToLeft = RightToLeft.Yes
            'translatedheaderlbl.RightToLeft = RightToLeft.Yes
            'transcribedheaderlbl.RightToLeft = RightToLeft.Yes
        End If

        Me.BackColor = My.Settings.subwindow_bgcolor

    End Sub
    Private Sub subtitlewindow_Resize(sender As Object, e As EventArgs) Handles MyBase.Resize
        ' Update MaximumSize of the labels when the form is resized
        Dim maxWidth = ClientSize.Width
        headertextlbl.MaximumSize = New Size(maxWidth, 0)
        'translatedheaderlbl.MaximumSize = New Size(maxWidth, 0)
        'transcribedheaderlbl.MaximumSize = New Size(maxWidth, 0)
    End Sub

    Private Sub subtitlewindow_FormClosing(sender As Object, e As FormClosingEventArgs) Handles MyBase.FormClosing
        InfoSaverTimer.Stop()
        cts.Cancel() ' Cancel any ongoing operations
        httpClient.Dispose()
        cts.Dispose() ' Dispose of the CancellationTokenSource
        Me.Dispose()
    End Sub

    Private Async Sub InfoSaverTimer_Tick(sender As Object, e As EventArgs) Handles InfoSaverTimer.Tick
        ' Check if the form is closing. If so, do not proceed with updates.
        If IsDisposed OrElse Disposing Then
            Return
        End If

        Dim headerText As String = String.Empty
        Dim translatedHeaderText As String = String.Empty
        Dim transcribedHeaderText As String = String.Empty
        Try
            If iOriginalText = True Then
                headerText = Await FetchTextFromUrl(URLHeader, cts.Token)
                Debug.WriteLine("Header Text: " & headerText)
            End If
        Catch ex As Exception
            Debug.WriteLine("Error fetching header text: " & ex.Message)
        End Try

        Try
            If iTranslateText = True Then
                translatedHeaderText = Await FetchTextFromUrl(URLTranslatedHeader, cts.Token)
                Debug.WriteLine("Translated Header Text: " & translatedHeaderText)
            End If
        Catch ex As Exception
            Debug.WriteLine("Error fetching translated header text: " & ex.Message)
        End Try

        Try
            If iTranscribeText = True Then
                transcribedHeaderText = Await FetchTextFromUrl(URLTranscribedHeader, cts.Token)
                Debug.WriteLine("Transcribed Header Text: " & transcribedHeaderText)
            End If
        Catch ex As Exception
            Debug.WriteLine("Error fetching transcribed header text: " & ex.Message)
        End Try

        ' Remove blacklisted phrases from each text
        headerText = RemoveBlacklistedPhrases(headerText)
        translatedHeaderText = RemoveBlacklistedPhrases(translatedHeaderText)
        transcribedHeaderText = RemoveBlacklistedPhrases(transcribedHeaderText)

        ' Before updating the UI, check if the form is still open and its handle is created
        If Not IsDisposed AndAlso Not Disposing AndAlso IsHandleCreated Then
            Try
                Invoke(Sub()
                           ' Build the text dynamically based on boolean flags
                           Dim displayText As String = String.Empty

                           If iOriginalText Then
                               displayText &= headerText
                           End If

                           If iTranslateText Then
                               If Not String.IsNullOrEmpty(displayText) Then
                                   displayText &= vbCrLf
                               End If
                               displayText &= translatedHeaderText
                           End If

                           If iTranscribeText Then
                               If Not String.IsNullOrEmpty(displayText) Then
                                   displayText &= vbCrLf
                               End If
                               displayText &= transcribedHeaderText
                           End If

                           ' Assign the constructed string to the label's text
                           headertextlbl.Text = displayText

                           ' Optionally update other labels if needed
                           ' translatedheaderlbl.Text = translatedHeaderText
                           ' transcribedheaderlbl.Text = transcribedHeaderText
                       End Sub)
            Catch ex As InvalidOperationException
                Debug.WriteLine("InvalidOperationException: " & ex.Message)
            Catch ex As Exception
                Debug.WriteLine("General Exception: " & ex.Message)
            End Try
        End If


        ' Check if the form is still valid for updating
        If Not IsDisposed AndAlso Not Disposing AndAlso IsHandleCreated Then
            Try
                Invoke(Sub()
                           ' Build the text dynamically based on boolean flags
                           Dim displayText As String = String.Empty

                           If iOriginalText Then
                               displayText &= headerText
                           End If

                           If iTranslateText Then
                               If Not String.IsNullOrEmpty(displayText) Then
                                   displayText &= vbCrLf
                               End If
                               displayText &= translatedHeaderText
                           End If

                           If iTranscribeText Then
                               If Not String.IsNullOrEmpty(displayText) Then
                                   displayText &= vbCrLf
                               End If
                               displayText &= transcribedHeaderText
                           End If

                           ' Assign the constructed string to the label's text
                           headertextlbl.Text = displayText

                           ' Optionally update other labels if needed
                           'translatedheaderlbl.Text = translatedHeaderText
                           'transcribedheaderlbl.Text = transcribedHeaderText

                           ' Force redraw
                           headertextlbl.Invalidate()
                           'translatedheaderlbl.Invalidate()
                           'transcribedheaderlbl.Invalidate()
                           Refresh()
                       End Sub)
            Catch ex As InvalidOperationException
                Debug.WriteLine("InvalidOperationException: " & ex.Message)
            Catch ex As Exception
                Debug.WriteLine("General Exception: " & ex.Message)
            End Try
        End If

    End Sub

    Private Function RemoveBlacklistedPhrases(text As String) As String
        ' Load blacklisted phrases from file
        Dim blacklistedPhrases As List(Of String) = LoadBlacklistedPhrases()

        If MainUI.WordBlockList.Checked = True Then
            ' Split the text into words
            Dim words As String() = text.Split(" "c)

            ' Iterate through each word
            For i As Integer = 0 To words.Length - 1
                ' Check if the word contains any blacklisted phrase
                For Each phrase As String In blacklistedPhrases
                    ' If the word contains the blacklisted phrase, replace it with an empty string
                    If words(i).IndexOf(phrase, StringComparison.OrdinalIgnoreCase) <> -1 Then
                        words(i) = ""
                        Exit For ' Exit loop if a blacklisted phrase is found in the word
                    End If
                Next
            Next

            ' Join the words back into a single string
            text = String.Join(" ", words)
        End If

        Return text
    End Function



    Private Function LoadBlacklistedPhrases() As List(Of String)
        Dim blacklistedPhrases As New List(Of String)()

        Try
            ' Read blacklisted phrases from file
            Dim lines As String() = File.ReadAllLines(MainUI.WordBlockListLocation)

            ' Add each line (phrase) to the list
            For Each line As String In lines
                blacklistedPhrases.Add(line.Trim())
            Next
        Catch ex As Exception
            Debug.WriteLine("Error loading blacklisted phrases: " & ex.Message)
        End Try

        Return blacklistedPhrases
    End Function

    Private Async Function FetchTextFromUrl(url As String, ct As CancellationToken) As Task(Of String)
        Try
            ' Directly returning the response string as it's just plain text
            Return Await httpClient.GetStringAsync(url, ct)
        Catch ex As OperationCanceledException
            Debug.WriteLine("Operation canceled")
            Return "Operation canceled"
        Catch ex As HttpRequestException
            Debug.WriteLine("HttpRequestException: " & ex.Message)
            Return "Error: " & ex.Message
        Catch ex As SocketException
            Debug.WriteLine("SocketException: " & ex.Message)
            Return "Error: " & ex.Message
        Catch ex As Exception
            Debug.WriteLine("General Exception: " & ex.Message)
            Return "Error: " & ex.Message
        End Try
    End Function

    Private Sub FontDialog1_Apply(sender As Object, e As EventArgs) Handles FontDialog1.Apply
        ' set Font, Font Style, Size, Effect, Script
        headertextlbl.Font = FontDialog1.Font
        'translatedheaderlbl.Font = FontDialog1.Font
        'transcribedheaderlbl.Font = FontDialog1.Font
    End Sub

    Private Sub FontFaceToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles FontFaceToolStripMenuItem.Click
        If FontDialog1.ShowDialog() = DialogResult.OK Then
            ' Apply the selected font to the labels
            headertextlbl.Font = FontDialog1.Font
            'translatedheaderlbl.Font = FontDialog1.Font
            'transcribedheaderlbl.Font = FontDialog1.Font
        End If
    End Sub

    Private Sub PlantToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles PlantToolStripMenuItem.Click
        Dim unused = MessageBox.Show("Help: " + vbCrLf + "Restore: Double Click then Right click the captions." + vbCrLf + vbCrLf + "Move: Click and Drag the captions", "Help Message")

        Main_BG_COLOR = Me.BackColor

        ' set transparency key to control
        TransparencyKey = Color.FromArgb(255, 255, 255)
        ' set background color to transparent
        BackColor = Color.FromArgb(255, 255, 255)
        ' set form boder style to none
        FormBorderStyle = FormBorderStyle.None
        ' set topmost to true
        TopMost = True

        MenuStrip1.Visible = False

        Opacity = 0.7

        Dragable = True

    End Sub

    Private Sub FrontToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles FrontToolStripMenuItem.Click
        ' Create a new ColorDialog instance
        Dim colorDialog As New ColorDialog()

        ' Show the color dialog and check if the user pressed OK
        If colorDialog.ShowDialog() = DialogResult.OK Then
            ' Apply the selected color to the labels
            headertextlbl.ForeColor = colorDialog.Color
            'translatedheaderlbl.ForeColor = colorDialog.Color
            'transcribedheaderlbl.ForeColor = colorDialog.Color
        End If
    End Sub

    Private Sub BackToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles BackToolStripMenuItem.Click
        ' Create a new ColorDialog instance
        Dim colorDialog As New ColorDialog()

        ' Show the color dialog and check if the user pressed OK
        If colorDialog.ShowDialog() = DialogResult.OK Then
            ' Apply the selected color to the background of the labels
            headertextlbl.BackColor = colorDialog.Color
            'translatedheaderlbl.BackColor = colorDialog.Color
            'transcribedheaderlbl.BackColor = colorDialog.Color
        End If
    End Sub

    Private Sub headertextlbl_MouseDoubleClick(sender As Object, e As MouseEventArgs) Handles headertextlbl.MouseDoubleClick
        ' Reset transparency key
        TransparencyKey = Color.Empty ' or the original color

        ' Reset background color
        BackColor = Main_BG_COLOR ' or the original color

        ' Reset form border style
        FormBorderStyle = FormBorderStyle.Sizable ' or the original style

        ' Reset topmost property
        TopMost = False

        ' Optionally, bring the form to the front
        BringToFront()

        MenuStrip1.Visible = True

        Opacity = 1

        Dragable = False
    End Sub

    Private Sub ShowToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem.Click
        'headertextlbl.Visible = True
        iOriginalText = True
    End Sub

    Private Sub HideToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem.Click
        'headertextlbl.Visible = False
        iOriginalText = False
    End Sub

    Private Sub ShowToolStripMenuItem1_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem1.Click
        'translatedheaderlbl.Visible = True
        iTranslateText = True
    End Sub

    Private Sub HideToolStripMenuItem1_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem1.Click
        'translatedheaderlbl.Visible = False
        iTranslateText = False
    End Sub

    Private Sub ShowToolStripMenuItem2_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem2.Click
        'transcribedheaderlbl.Visible = True
        iTranscribeText = True
    End Sub
    Private Sub HideToolStripMenuItem2_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem2.Click
        'transcribedheaderlbl.Visible = False
        iTranscribeText = False
    End Sub

    Private Sub headertextlbl_MouseDown(sender As Object, e As MouseEventArgs) Handles headertextlbl.MouseDown
        If e.Button = MouseButtons.Left And Dragable = True Then
            Dim unused1 = ReleaseCapture()
            Dim unused = SendMessage(Handle, &H112, &HF012, 0)
        End If
    End Sub

    Private Sub TopTextToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles TopTextToolStripMenuItem.Click
        'headertextlbl.Dock = DockStyle.Top
        'translatedheaderlbl.Dock = DockStyle.Top
        'transcribedheaderlbl.Dock = DockStyle.Top
        headertextlbl.TextAlign = ContentAlignment.TopLeft
    End Sub

    Private Sub BottomTextToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles BottomTextToolStripMenuItem.Click
        'headertextlbl.Dock = DockStyle.Bottom
        'translatedheaderlbl.Dock = DockStyle.Bottom
        'transcribedheaderlbl.Dock = DockStyle.Bottom
        headertextlbl.TextAlign = ContentAlignment.BottomLeft
    End Sub
    Private Sub RightToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles RightToolStripMenuItem.Click
        'headertextlbl.Dock = DockStyle.Right
        'translatedheaderlbl.Dock = DockStyle.Right
        'transcribedheaderlbl.Dock = DockStyle.Right
        'transcribedheaderlbl.BringToFront()
        headertextlbl.TextAlign = ContentAlignment.TopRight
    End Sub


    Private Sub LeftToolStripMenuItem1_Click(sender As Object, e As EventArgs) Handles LeftToolStripMenuItem1.Click
        headertextlbl.RightToLeft = RightToLeft.No
        'translatedheaderlbl.RightToLeft = RightToLeft.No
        'transcribedheaderlbl.RightToLeft = RightToLeft.No
        RTL_Mode = False
    End Sub

    Private Sub RightToLeftToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles RightToLeftToolStripMenuItem.Click
        headertextlbl.RightToLeft = RightToLeft.Yes
        'translatedheaderlbl.RightToLeft = RightToLeft.Yes
        'transcribedheaderlbl.RightToLeft = RightToLeft.Yes
        RTL_Mode = True
    End Sub


    Private Sub BG_Color_Click(sender As Object, e As EventArgs) Handles BG_Color.Click
        ColorDialog1.ShowDialog()
        Me.BackColor = ColorDialog1.Color
    End Sub

    Private Sub ResetBGColor_Click(sender As Object, e As EventArgs) Handles ResetBGColor.Click
        Me.BackColor = Color.FromArgb(0, 177, 64)
    End Sub

    Private Sub ResetCWindow_Click(sender As Object, e As EventArgs)

    End Sub

    Private Sub SaveToolStripMenuItem3_Click(sender As Object, e As EventArgs) Handles SaveToolStripMenuItem3.Click
        My.Settings.headertextlbl_font = headertextlbl.Font
        My.Settings.headertextlbl_forecolor = headertextlbl.ForeColor
        My.Settings.headertextlbl_backcolor = headertextlbl.BackColor
        My.Settings.subwindow_lmode = RTL_Mode
        My.Settings.subwindow_bgcolor = Me.BackColor
        My.Settings.Save()
        My.Settings.Reload()
        MessageBox.Show("Your captions window settings were saved.", "Saved")
    End Sub

    Private Sub ResetToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles ResetToolStripMenuItem.Click
        With My.Settings
            .headertextlbl_font = New FontConverter().ConvertFromString(My.Settings.Properties("headertextlbl_font").DefaultValue.ToString())
            .translatedheaderlbl_font = New FontConverter().ConvertFromString(My.Settings.Properties("translatedheaderlbl_font").DefaultValue.ToString())
            .transcribedheaderlbl_font = New FontConverter().ConvertFromString(My.Settings.Properties("transcribedheaderlbl_font").DefaultValue.ToString())

            ' Reset color settings
            .headertextlbl_forecolor = Color.FromName(My.Settings.Properties("headertextlbl_forecolor").DefaultValue.ToString())
            .headertextlbl_backcolor = Color.FromName(My.Settings.Properties("headertextlbl_backcolor").DefaultValue.ToString())
            .translatedheaderlbl_forecolor = Color.FromName(My.Settings.Properties("translatedheaderlbl_forecolor").DefaultValue.ToString())
            .translatedheaderlbl_backcolor = Color.FromName(My.Settings.Properties("translatedheaderlbl_backcolor").DefaultValue.ToString())
            .transcribedheaderlbl_forecolor = Color.FromName(My.Settings.Properties("transcribedheaderlbl_forecolor").DefaultValue.ToString())
            .transcribedheaderlbl_backcolor = Color.FromName(My.Settings.Properties("transcribedheaderlbl_backcolor").DefaultValue.ToString())

            .subwindow_bgcolor = Color.FromName(My.Settings.Properties("subwindow_bgcolor").DefaultValue.ToString())

            .subwindow_lmode = False

            .Save()
            .Reload()
            Dim Cwindows As New subtitlewindow()
            Cwindows.Show()
            Me.Close()
        End With
    End Sub

    Private Sub BottomRightToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles BottomRightToolStripMenuItem.Click
        headertextlbl.TextAlign = ContentAlignment.BottomRight
    End Sub
    Private Sub Panel1_MouseDown(sender As Object, e As MouseEventArgs) Handles Panel1.MouseDown
        If e.Button = MouseButtons.Left Then
            ' Determine which corner is being clicked
            If e.X >= Panel1.Width - 10 And e.Y >= Panel1.Height - 10 Then
                resizableCorner = "bottom-right"
            ElseIf e.X <= 10 And e.Y >= Panel1.Height - 10 Then
                resizableCorner = "bottom-left"
            ElseIf e.X >= Panel1.Width - 10 And e.Y <= 10 Then
                resizableCorner = "top-right"
            ElseIf e.X <= 10 And e.Y <= 10 Then
                resizableCorner = "top-left"
            End If

            If resizableCorner <> "" Then
                resizing = True
                startPoint = e.Location
                startSize = Panel1.Size
                startLocation = Panel1.Location
            End If
        End If
    End Sub

    Private Sub Panel1_MouseMove(sender As Object, e As MouseEventArgs) Handles Panel1.MouseMove
        If resizing Then
            ' Visual feedback or guidelines can be added here if necessary
            Me.Opacity = 0.7
        Else
            ' Change cursor based on position
            If e.X >= Panel1.Width - 10 And e.Y >= Panel1.Height - 10 Then
                Panel1.Cursor = Cursors.SizeNWSE
            ElseIf e.X <= 10 And e.Y >= Panel1.Height - 10 Then
                Panel1.Cursor = Cursors.SizeNESW
            ElseIf e.X >= Panel1.Width - 10 And e.Y <= 10 Then
                Panel1.Cursor = Cursors.SizeNESW
            ElseIf e.X <= 10 And e.Y <= 10 Then
                Panel1.Cursor = Cursors.SizeNWSE
            Else
                Panel1.Cursor = Cursors.Default
            End If
        End If
    End Sub

    Private Sub Panel1_MouseUp(sender As Object, e As MouseEventArgs) Handles Panel1.MouseUp
        If resizing Then
            endPoint = Panel1.PointToClient(MousePosition)
            Select Case resizableCorner
                Case "bottom-right"
                    Panel1.Size = New Size(startSize.Width + (endPoint.X - startPoint.X), startSize.Height + (endPoint.Y - startPoint.Y))
                Case "bottom-left"
                    Panel1.Location = New Point(startLocation.X + (endPoint.X - startPoint.X), startLocation.Y)
                    Panel1.Size = New Size(startSize.Width - (endPoint.X - startPoint.X), startSize.Height + (endPoint.Y - startPoint.Y))
                Case "top-right"
                    Panel1.Location = New Point(startLocation.X, startLocation.Y + (endPoint.Y - startPoint.Y))
                    Panel1.Size = New Size(startSize.Width + (endPoint.X - startPoint.X), startSize.Height - (endPoint.Y - startPoint.Y))
                Case "top-left"
                    Panel1.Location = New Point(startLocation.X + (endPoint.X - startPoint.X), startLocation.Y + (endPoint.Y - startPoint.Y))
                    Panel1.Size = New Size(startSize.Width - (endPoint.X - startPoint.X), startSize.Height - (endPoint.Y - startPoint.Y))
            End Select
            resizing = False
            resizableCorner = ""
            Me.Opacity = 1
        End If
    End Sub

    Private Sub MakeBackgroundInvisablToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles MakeBackgroundInvisablToolStripMenuItem.Click
        Me.TransparencyKey = Me.BackColor
    End Sub
End Class
