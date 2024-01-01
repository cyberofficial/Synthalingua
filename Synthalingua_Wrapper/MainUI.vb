Imports System.Linq.Expressions
' using the system file storage
Imports System.IO

Public Class MainUI

    Dim PrimaryFolder As String
    Dim ShortCutType As String
    Private Sub Button2_Click(sender As Object, e As EventArgs) Handles Button2.Click
        If Label1.ForeColor = Color.Red Then
            Label1.ForeColor = Color.Black
        End If
        OpenScriptDiag.ShowDialog()
        ScriptFileLocation.Text = OpenScriptDiag.FileName
        PrimaryFolder = System.IO.Path.GetDirectoryName(OpenScriptDiag.FileName)
        ' Check file name as .py or .exe, if py ShortCutType is Source else ShortCutType is Portable
        If System.IO.Path.GetExtension(OpenScriptDiag.FileName) = ".py" Then
            ShortCutType = "Source"
        Else
            ShortCutType = "Portable"
        End If
    End Sub

    Private Sub ChunkSizeTrackBar_ValueChanged(sender As Object, e As EventArgs) Handles ChunkSizeTrackBar.ValueChanged
        ChunkSizeTrackBarValue.Text = "Chunks: " & ChunkSizeTrackBar.Value
    End Sub

    Private Sub GenerateConfigButton_Click(sender As Object, e As EventArgs) Handles GenerateConfigButton.Click
        If ScriptFileLocation.Text = "" Then
            MsgBox("Please select the program file.")
            Exit Sub
        End If
        ConfigTextBox.Text = "" & vbNewLine & "cls" & vbNewLine & "@echo off" & vbNewLine & "Echo Loading Script" & vbNewLine
        If ShortCutType = "Source" Then
            ConfigTextBox.Text += "call " & PrimaryFolder & "\data_whisper\Scripts\activate.bat" & vbNewLine
            ConfigTextBox.Text += "python """ & PrimaryFolder & "\transcribe_audio.py"" "
        Else
            ConfigTextBox.Text += """" & PrimaryFolder & "\transcribe_audio.exe"" "
        End If

        ConfigTextBox.Text += "--ram " & RamSize.Text & " "

        If MIC_RadioButton.Checked = True Then
            ConfigTextBox.Text += "--microphone_enabled true "
            If MicEnCheckBox.Checked = True Then
                ConfigTextBox.Text += "--energy_threshold " & EnThreshValue.Value & " "
            End If
            If MicCaliCheckBox.Checked = True Then
                ConfigTextBox.Text += "--mic_calibration_time " & MicCaliTime.Value & " "
            End If
            If RecordTimeOutCHeckBox.Checked = True Then
                ConfigTextBox.Text += "--record_timeout " & RecordTimeout.Value & " "
            End If
            If PhraseTimeOutCheckbox.Checked = True Then
                ConfigTextBox.Text += "--phrase_timeout " & PhraseTimeout.Value & " "
            End If
            ConfigTextBox.Text += "--set_microphone " & MicID.Value & " "
        End If

        If HSL_RadioButton.Checked = True Then
            If ShowOriginalText.Checked = True Then
                ConfigTextBox.Text += "--stream_original_text "
            End If
        End If

        If ForceRam.Checked = True Then
            ConfigTextBox.Text += "--ramforce " & " "
        End If

        If HSL_RadioButton.Checked = True Then
            ConfigTextBox.Text += "--stream """ & HLS_URL.Text & """ "
        End If

        If HSL_RadioButton.Checked = True Then
            If StreamLanguage.Text = "--Auto Detect--" Then
                ' do nothing for now
            Else
                ConfigTextBox.Text += "--stream_language " & StreamLanguage.Text & " "
            End If
        Else
            If StreamLanguage.Text = "--Auto Detect--" Then
                ' do nothing for now
            Else
                ConfigTextBox.Text += "--language " & StreamLanguage.Text & " "
            End If
        End If

        'If HSL_RadioButton.Checked = True Then
        '    ConfigTextBox.Text += "--stream_language " & StreamLanguage.Text & " "
        'Else
        '    ConfigTextBox.Text += "--language " & StreamLanguage.Text & " "
        'End If

        If EnglishTranslationCheckBox.Checked = True Then
            If HSL_RadioButton.Checked = True Then
                ConfigTextBox.Text += "--stream_translate "
            Else
                ConfigTextBox.Text += "--translate "
            End If
        End If

        If HSL_RadioButton.Checked = True Then
            If SecondaryTranslation.Checked = True Then
                ConfigTextBox.Text += "--stream_transcribe "
                ConfigTextBox.Text += "--stream_target_language " & SecondaryTranslationLanguage.Text & " "
            End If
        Else
            If SecondaryTranslation.Checked = True Then
                ConfigTextBox.Text += "--transcribe "
                ConfigTextBox.Text += "--target_language " & SecondaryTranslationLanguage.Text & " "
            End If
        End If

        If HSL_RadioButton.Checked = True Then
            ConfigTextBox.Text += "--stream_chunks " & ChunkSizeTrackBar.Value & " "
        End If

        If CUDA_RadioButton.Checked = True Then
            ConfigTextBox.Text += "--device cuda "
        End If

        If CPU_RadioButton.Checked = True Then
            ConfigTextBox.Text += "--device cpu "
        End If

        If CookiesName.Text <> "" Then
            ConfigTextBox.Text += "--cookies " & CookiesName.Text & " "
        End If

        If WebServerButton.Checked = True Then
            ConfigTextBox.Text += "--portnumber " & PortNumber.Value & " "
        End If

        If DiscordWebHook.Text <> "" Then
            ConfigTextBox.Text += "--discord_webhook """ & DiscordWebHook.Text & """" & " "
        End If

    End Sub

    Private Sub SaveConfigToFileButton_Click(sender As Object, e As EventArgs) Handles SaveConfigToFileButton.Click
        SaveFileDialog.Filter = "Batch File|*.bat"
        SaveFileDialog.Title = "Save Config File"
        SaveFileDialog.ShowDialog()
        If SaveFileDialog.FileName <> "" Then
            My.Computer.FileSystem.WriteAllText(SaveFileDialog.FileName, ConfigTextBox.Text, False)
        End If
    End Sub

    Private Sub RunScript_Click(sender As Object, e As EventArgs) Handles RunScript.Click
        If ScriptFileLocation.Text = "" Then
            MsgBox("Please select the program file.")
            Exit Sub
        End If

        ' save ConfigTextBox.Text to a tmp bat file in the primary folder then run it
        Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
        File.WriteAllText(tmpBatFile, ConfigTextBox.Text)
        Process.Start(tmpBatFile)
    End Sub

    Private Sub microphone_id_button_Click(sender As Object, e As EventArgs) Handles microphone_id_button.Click
        Try
            If MIC_RadioButton.Checked = True Then
                Try
                    If ScriptFileLocation.Text.Contains(" ") Then
                        MsgBox("Please select a program file that does not have spaces in the file path.")
                        Exit Sub
                    End If
                    If ScriptFileLocation.Text.Contains(".py") Then
                        Dim TempCommand As String = "call " & PrimaryFolder & "\data_whisper\Scripts\activate.bat"" " & vbNewLine & "python """ & ScriptFileLocation.Text & """ --microphone_enabled true --list_microphones"
                        Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
                        File.WriteAllText(tmpBatFile, TempCommand)
                        Process.Start(tmpBatFile)
                    Else
                        MessageBox.Show("Running command: " & ScriptFileLocation.Text & " --microphone_enabled true --list_microphones")
                        ' add a pause to the end of the command so the user can see the output
                        Dim TempCommand As String = """" & ScriptFileLocation.Text & """ --microphone_enabled true --list_microphones" & vbNewLine & "pause"
                        Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
                        File.WriteAllText(tmpBatFile, TempCommand)
                        Process.Start(tmpBatFile)
                    End If

                Catch ex As Exception
                    MessageBox.Show("Error: " & ex.Message)
                    MessageBox.Show("Possible error is that the program path is not valid, or is missing a file. Make sure to select the program file.")
                    ' make Label1 flash black and red
                    Dim t As New Timer
                    t.Interval = 100
                    AddHandler t.Tick, Sub()
                                            If Label1.ForeColor = Color.Black Then
                                                Label1.ForeColor = Color.Red
                                            Else
                                                Label1.ForeColor = Color.Black
                                            End If
                                        End Sub
                    t.Start()
                    ' stop the timer after 5 seconds
                    Dim t2 As New Timer
                    t2.Interval = 5000
                    AddHandler t2.Tick, Sub()
                                             t.Stop()
                                         End Sub
                    t2.Start()
                End Try
            Else
                MsgBox("Please select the microphone option")
            End If
        Catch ex As Exception
            MessageBox.Show("Error: " & ex.Message)
        End Try

    End Sub

    Private Sub WebLinkOG_Click(sender As Object, e As EventArgs) Handles WebLinkOG.Click
        Clipboard.SetText("http://localhost:" & PortNumber.Value & "?showoriginal")
        MessageBox.Show("Copied http://localhost:" & PortNumber.Value & "?showoriginal to clipboard")
    End Sub

    Private Sub WebLinkT1_Click(sender As Object, e As EventArgs) Handles WebLinkT1.Click
        Clipboard.SetText("http://localhost:" & PortNumber.Value & "?showtranslation ")
        MessageBox.Show("Copied http://localhost:" & PortNumber.Value & "?showtranslation to clipboard")
    End Sub

    Private Sub WebLinkT2_Click(sender As Object, e As EventArgs) Handles WebLinkT2.Click
        Clipboard.SetText("http://localhost:" & PortNumber.Value & "?showtranscription  ")
        MessageBox.Show("Copied http://localhost:" & PortNumber.Value & "?showtranscription to clipboard")
    End Sub

    Private Sub MainUI_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        ' if the folder 'cookies' exist then populate CookiesName with each file name in there exclusding the file extension
        If Directory.Exists(Path.Combine(Application.StartupPath, "cookies")) Then
            For Each file As String In Directory.GetFiles(Path.Combine(Application.StartupPath, "cookies"))
                CookiesName.Items.Add(Path.GetFileNameWithoutExtension(file))
            Next
        End If
    End Sub

    Private Sub CookiesRefresh_Click(sender As Object, e As EventArgs) Handles CookiesRefresh.Click
        ' refresh the CookiesName by clearing it and then repopulating it
        CookiesName.Items.Clear()
        If Directory.Exists(Path.Combine(Application.StartupPath, "cookies")) Then
            For Each file As String In Directory.GetFiles(Path.Combine(Application.StartupPath, "cookies"))
                CookiesName.Items.Add(Path.GetFileNameWithoutExtension(file))
            Next
        End If
    End Sub

    Private Sub CookiesRefresh_MouseHover(sender As Object, e As EventArgs) Handles CookiesRefresh.MouseHover
        ' shows a little tooltip when you hover over the button that says "Refresh Cookies"
        ToolTip1.SetToolTip(CookiesRefresh, "Clear the set cookie.")
    End Sub

    Private Sub Button2_MouseHover(sender As Object, e As EventArgs) Handles Button2.MouseHover
        ToolTip1.SetToolTip(Button2, "Select the propgram file.")
    End Sub

    Private Sub WebLinkOG_MouseHover(sender As Object, e As EventArgs) Handles WebLinkOG.MouseHover
        ToolTip1.SetToolTip(WebLinkOG, "Copy the link to the clipboard. Will copy http://localhost:" & PortNumber.Value & "?showoriginal")
    End Sub

    Private Sub WebLinkT1_MouseHover(sender As Object, e As EventArgs) Handles WebLinkT1.MouseHover
        ToolTip1.SetToolTip(WebLinkT1, "Copy the link to the clipboard. Will copy http://localhost:" & PortNumber.Value & "?showtranslation")
    End Sub

    Private Sub WebLinkT2_MouseHover(sender As Object, e As EventArgs) Handles WebLinkT2.MouseHover
        ToolTip1.SetToolTip(WebLinkT2, "Copy the link to the clipboard. Will copy http://localhost:" & PortNumber.Value & "?showtranscription")
    End Sub

    Private Sub CheckBoxCMDBLock_CheckedChanged(sender As Object, e As EventArgs) Handles CheckBoxCMDBLock.CheckedChanged
        If CheckBoxCMDBLock.Checked = False Then
            ConfigTextBox.Visible = False
        Else
            ConfigTextBox.Visible = True

        End If
    End Sub

    Private Sub HSL_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles HSL_RadioButton.MouseHover
        ToolTip1.SetToolTip(HSL_RadioButton, "Use HLS stream instead of microphone. HLS stream is a stream of audio from a website.")
    End Sub

    Private Sub MIC_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles MIC_RadioButton.MouseHover
        ToolTip1.SetToolTip(MIC_RadioButton, "Use microphone instead of HLS stream.")
    End Sub

    Private Sub CUDA_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles CUDA_RadioButton.MouseHover
        ToolTip1.SetToolTip(CUDA_RadioButton, "Use CUDA for speech recognition. More powerful but requires a GPU.")
    End Sub

    Private Sub CPU_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles CPU_RadioButton.MouseHover
        ToolTip1.SetToolTip(CPU_RadioButton, "Use CPU for speech recognition. Less powerful but does not require a GPU.")
    End Sub

    Private Sub WebServerButton_MouseHover(sender As Object, e As EventArgs) Handles WebServerButton.MouseHover
        ToolTip1.SetToolTip(WebServerButton, "Enable the web server. This will allow you to view the output of the program in a web browser.")
    End Sub

    Private Sub RamSize_MouseHover(sender As Object, e As EventArgs) Handles RamSize.MouseHover
        ToolTip1.SetToolTip(RamSize, "Set the amount of V-RAM to use for the program. This is in GB. The higher the number the more RAM it will use but the more accurate it will be.")
    End Sub

    Private Sub CookiesName_MouseHover(sender As Object, e As EventArgs) Handles CookiesName.MouseHover
        ToolTip1.SetToolTip(CookiesName, "Set the cookie to use for the program. This will allow you to use a premium account.")
    End Sub

    Private Sub StreamLanguage_MouseHover(sender As Object, e As EventArgs) Handles StreamLanguage.MouseHover
        ToolTip1.SetToolTip(StreamLanguage, "Set the language of the stream. This is the language that the stream is in.")
    End Sub

    Private Sub EnglishTranslationCheckBox_MouseHover(sender As Object, e As EventArgs) Handles EnglishTranslationCheckBox.MouseHover
        ToolTip1.SetToolTip(EnglishTranslationCheckBox, "Enable English translation. This will translate the stream to English.")
    End Sub

    Private Sub SecondaryTranslationLanguage_MouseHover(sender As Object, e As EventArgs) Handles SecondaryTranslationLanguage.MouseHover
        ToolTip1.SetToolTip(SecondaryTranslationLanguage, "Set the language to translate the stream to. This is the language that the stream will be translated to.")
    End Sub

    Private Sub DiscordWebHook_MouseHover(sender As Object, e As EventArgs) Handles DiscordWebHook.MouseHover
        ToolTip1.SetToolTip(DiscordWebHook, "Set the discord webhook to use. This will send the output of the program to a discord channel.")
    End Sub

    Private Sub HLS_URL_MouseHover(sender As Object, e As EventArgs) Handles HLS_URL.MouseHover
        ToolTip1.SetToolTip(HLS_URL, "Set the HLS stream URL to use. This is the URL of the stream. Example: https://example.com/stream")
    End Sub

    Private Sub ChunkSizeTrackBar_MouseHover(sender As Object, e As EventArgs) Handles ChunkSizeTrackBar.MouseHover
        ToolTip1.SetToolTip(ChunkSizeTrackBar, "Set the chunk size. This is the amount of audio to process at once. The higher the number the more accurate it will be but the more delay there will be.")
    End Sub

    Private Sub ShowOriginalText_MouseHover(sender As Object, e As EventArgs) Handles ShowOriginalText.MouseHover
        ToolTip1.SetToolTip(ShowOriginalText, "Show the original text of the stream. This will show the original text of the stream. So if the speaker is speaking Japanese it will show the Japanese text.")
    End Sub

    Private Sub Energy_Threshold_MouseClick(sender As Object, e As MouseEventArgs) Handles Energy_Threshold.MouseClick
        MessageBox.Show("Set the energy threshold. This is the amount of energy required to start recording. The higher the number the more energy is required to start recording.")
    End Sub

    Private Sub MicCaliLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles MicCaliLbl.MouseClick
        MessageBox.Show("Set the microphone calibration time. This is the amount of time to calibrate the microphone. The higher the number the more time it will take to calibrate the microphone.")
    End Sub

    Private Sub RecordTimeoutLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles RecordTimeoutLbl.MouseClick
        MessageBox.Show("Set the record timeout. This is the amount of time to record for. The higher the number the more time it will record for.")
    End Sub

    Private Sub PhraseTimeOutlbl_MouseClick(sender As Object, e As MouseEventArgs) Handles PhraseTimeOutlbl.MouseClick
        MessageBox.Show("Set the phrase timeout. This is the amount of time to wait for a phrase. The higher the number the more time it will wait for a phrase. How many sentences in a paragraph it'll show.")
    End Sub

    Private Sub SetMicLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles SetMicLbl.MouseClick
        MessageBox.Show("Set the microphone to use. This is the microphone to use. The higher the number the more time it will wait for a phrase.")
    End Sub
End Class
