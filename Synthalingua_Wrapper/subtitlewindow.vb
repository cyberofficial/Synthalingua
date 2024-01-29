Imports System.Net.Http
Imports System.Net.Sockets
Imports System.Threading
Imports System.Runtime.InteropServices


Public Class subtitlewindow
    Private httpClient As HttpClient
    Private cts As CancellationTokenSource

    ' Declare variables for URLs
    Private URLHeader As String
    Private URLTranslatedHeader As String
    Private URLTranscribedHeader As String


    ' P/Invoke declarations
    <DllImport("user32.dll")>
    Public Shared Function SendMessage(hWnd As IntPtr, Msg As Integer, wParam As Integer, lParam As Integer) As Integer
    End Function

    <DllImport("user32.dll")>
    Public Shared Function ReleaseCapture() As Boolean
    End Function

    Public Sub New()
        ' This call is required by the designer.
        InitializeComponent()

        ' Initialize HttpClient and CancellationTokenSource
        httpClient = New HttpClient()
        cts = New CancellationTokenSource()

        ' Set the port number from MainUI and initialize URLs
        Dim SubPortNumber As String = MainUI.PortNumber.Value.ToString()
        URLHeader = $"http://localhost:{SubPortNumber}/update-header"
        URLTranslatedHeader = $"http://localhost:{SubPortNumber}/update-translated-header"
        URLTranscribedHeader = $"http://localhost:{SubPortNumber}/update-transcribed-header"

        ' Initialize label properties for auto-wrapping
        InitializeLabelWrapping(headertextlbl)
        InitializeLabelWrapping(translatedheaderlbl)
        InitializeLabelWrapping(transcribedheaderlbl)
    End Sub

    Private Sub InitializeLabelWrapping(label As Label)
        label.AutoSize = True
        label.AutoEllipsis = True
        label.MaximumSize = New Size(Me.ClientSize.Width, 0)
    End Sub

    Private Sub subtitlewindow_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        InfoSaverTimer.Interval = 50 ' Set your timer interval to 50ms
        InfoSaverTimer.Start()
    End Sub
    Private Sub subtitlewindow_Resize(sender As Object, e As EventArgs) Handles MyBase.Resize
        ' Update MaximumSize of the labels when the form is resized
        Dim maxWidth = ClientSize.Width
        headertextlbl.MaximumSize = New Size(maxWidth, 0)
        translatedheaderlbl.MaximumSize = New Size(maxWidth, 0)
        transcribedheaderlbl.MaximumSize = New Size(maxWidth, 0)
    End Sub

    Private Sub subtitlewindow_FormClosing(sender As Object, e As FormClosingEventArgs) Handles MyBase.FormClosing
        InfoSaverTimer.Stop()
        cts.Cancel() ' Cancel any ongoing operations
        httpClient.Dispose()
        cts.Dispose() ' Dispose of the CancellationTokenSource
    End Sub

    Private Async Sub InfoSaverTimer_Tick(sender As Object, e As EventArgs) Handles InfoSaverTimer.Tick
        ' Check if the form is closing. If so, do not proceed with updates.
        If Me.IsDisposed OrElse Me.Disposing Then
            Return
        End If

        Dim headerText As String = String.Empty
        Dim translatedHeaderText As String = String.Empty
        Dim transcribedHeaderText As String = String.Empty

        Try
            headerText = Await FetchTextFromUrl(URLHeader, cts.Token)
            Debug.WriteLine("Header Text: " & headerText)
        Catch ex As Exception
            Debug.WriteLine("Error fetching header text: " & ex.Message)
        End Try

        Try
            translatedHeaderText = Await FetchTextFromUrl(URLTranslatedHeader, cts.Token)
            Debug.WriteLine("Translated Header Text: " & translatedHeaderText)
        Catch ex As Exception
            Debug.WriteLine("Error fetching translated header text: " & ex.Message)
        End Try

        Try
            transcribedHeaderText = Await FetchTextFromUrl(URLTranscribedHeader, cts.Token)
            Debug.WriteLine("Transcribed Header Text: " & transcribedHeaderText)
        Catch ex As Exception
            Debug.WriteLine("Error fetching transcribed header text: " & ex.Message)
        End Try

        ' Before updating the UI, check if the form is still open and its handle is created
        If Not Me.IsDisposed AndAlso Not Me.Disposing AndAlso Me.IsHandleCreated Then
            Try
                Me.Invoke(Sub()
                              headertextlbl.Text = headerText
                              translatedheaderlbl.Text = translatedHeaderText
                              transcribedheaderlbl.Text = transcribedHeaderText
                          End Sub)
            Catch ex As InvalidOperationException
                Debug.WriteLine("InvalidOperationException: " & ex.Message)
            Catch ex As Exception
                Debug.WriteLine("General Exception: " & ex.Message)
            End Try
        End If

        ' Check if the form is still valid for updating
        If Not Me.IsDisposed AndAlso Not Me.Disposing AndAlso Me.IsHandleCreated Then
            Try
                Me.Invoke(Sub()
                              headertextlbl.Text = headerText
                              translatedheaderlbl.Text = translatedHeaderText
                              transcribedheaderlbl.Text = transcribedHeaderText

                              ' Force redraw
                              headertextlbl.Invalidate()
                              translatedheaderlbl.Invalidate()
                              transcribedheaderlbl.Invalidate()
                              Me.Refresh()
                          End Sub)
            Catch ex As InvalidOperationException
                Debug.WriteLine("InvalidOperationException: " & ex.Message)
            Catch ex As Exception
                Debug.WriteLine("General Exception: " & ex.Message)
            End Try
        End If
    End Sub

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
        translatedheaderlbl.Font = FontDialog1.Font
        transcribedheaderlbl.Font = FontDialog1.Font
    End Sub

    Private Sub FontFaceToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles FontFaceToolStripMenuItem.Click
        If FontDialog1.ShowDialog() = DialogResult.OK Then
            ' Apply the selected font to the labels
            headertextlbl.Font = FontDialog1.Font
            translatedheaderlbl.Font = FontDialog1.Font
            transcribedheaderlbl.Font = FontDialog1.Font
        End If
    End Sub

    Private Sub PlantToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles PlantToolStripMenuItem.Click
        MessageBox.Show("Help: " + vbCrLf + "Restore: Double Click then Right click the captions." + vbCrLf + vbCrLf + "Move: Click and Drag the captions", "Help Message")

        ' set transparency key to control
        Me.TransparencyKey = Color.FromArgb(255, 255, 255)
        ' set background color to transparent
        Me.BackColor = Color.FromArgb(255, 255, 255)
        ' set form boder style to none
        Me.FormBorderStyle = FormBorderStyle.None
        ' set topmost to true
        Me.TopMost = True

        MenuStrip1.Visible = False

        Me.Opacity = 0.65

    End Sub

    Private Sub FrontToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles FrontToolStripMenuItem.Click
        ' Create a new ColorDialog instance
        Dim colorDialog As New ColorDialog()

        ' Show the color dialog and check if the user pressed OK
        If colorDialog.ShowDialog() = DialogResult.OK Then
            ' Apply the selected color to the labels
            headertextlbl.ForeColor = colorDialog.Color
            translatedheaderlbl.ForeColor = colorDialog.Color
            transcribedheaderlbl.ForeColor = colorDialog.Color
        End If
    End Sub

    Private Sub BackToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles BackToolStripMenuItem.Click
        ' Create a new ColorDialog instance
        Dim colorDialog As New ColorDialog()

        ' Show the color dialog and check if the user pressed OK
        If colorDialog.ShowDialog() = DialogResult.OK Then
            ' Apply the selected color to the background of the labels
            headertextlbl.BackColor = colorDialog.Color
            translatedheaderlbl.BackColor = colorDialog.Color
            transcribedheaderlbl.BackColor = colorDialog.Color
        End If
    End Sub

    Private Sub headertextlbl_MouseDoubleClick(sender As Object, e As MouseEventArgs) Handles headertextlbl.MouseDoubleClick, translatedheaderlbl.MouseDoubleClick, transcribedheaderlbl.MouseDoubleClick
        ' Reset transparency key
        Me.TransparencyKey = Color.Empty ' or the original color

        ' Reset background color
        Me.BackColor = SystemColors.Control ' or the original color

        ' Reset form border style
        Me.FormBorderStyle = FormBorderStyle.Sizable ' or the original style

        ' Reset topmost property
        Me.TopMost = False

        ' Optionally, bring the form to the front
        Me.BringToFront()

        MenuStrip1.Visible = True

        Me.Opacity = 1
    End Sub

    Private Sub ShowToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem.Click
        headertextlbl.Visible = True
    End Sub

    Private Sub HideToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem.Click
        headertextlbl.Visible = False
    End Sub

    Private Sub ShowToolStripMenuItem1_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem1.Click
        translatedheaderlbl.Visible = True
    End Sub

    Private Sub HideToolStripMenuItem1_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem1.Click
        translatedheaderlbl.Visible = False
    End Sub

    Private Sub ShowToolStripMenuItem2_Click(sender As Object, e As EventArgs) Handles ShowToolStripMenuItem2.Click
        transcribedheaderlbl.Visible = True
    End Sub
    Private Sub HideToolStripMenuItem2_Click(sender As Object, e As EventArgs) Handles HideToolStripMenuItem2.Click
        transcribedheaderlbl.Visible = False
    End Sub

    Private Sub headertextlbl_MouseDown(sender As Object, e As MouseEventArgs) Handles headertextlbl.MouseDown, translatedheaderlbl.MouseDown, transcribedheaderlbl.MouseDown
        If e.Button = MouseButtons.Left Then
            ReleaseCapture()
            SendMessage(Handle, &H112, &HF012, 0)
        End If
    End Sub

    Private Sub TopTextToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles TopTextToolStripMenuItem.Click
        headertextlbl.Dock = DockStyle.Top
        translatedheaderlbl.Dock = DockStyle.Top
        transcribedheaderlbl.Dock = DockStyle.Top
    End Sub

    Private Sub BottomTextToolStripMenuItem_Click(sender As Object, e As EventArgs) Handles BottomTextToolStripMenuItem.Click
        headertextlbl.Dock = DockStyle.Bottom
        translatedheaderlbl.Dock = DockStyle.Bottom
        transcribedheaderlbl.Dock = DockStyle.Bottom
    End Sub
End Class
