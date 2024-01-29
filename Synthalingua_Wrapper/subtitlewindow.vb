Imports System.Net.Http
Imports System.Net.Sockets
Imports System.Threading

Public Class subtitlewindow
    Private httpClient As HttpClient
    Private cts As CancellationTokenSource
    Private Const URLHeader As String = "http://localhost:2000/update-header"
    Private Const URLTranslatedHeader As String = "http://localhost:2000/update-translated-header"
    Private Const URLTranscribedHeader As String = "http://localhost:2000/update-transcribed-header"

    Public Sub New()
        ' This call is required by the designer.
        InitializeComponent()

        ' Add any initialization after the InitializeComponent() call.
        httpClient = New HttpClient()
        cts = New CancellationTokenSource()
    End Sub

    Private Sub subtitlewindow_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        InfoSaverTimer.Interval = 50 ' Set your timer interval to 50ms
        InfoSaverTimer.Start()
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

End Class
