Imports System.Linq.Expressions
' using the system file storage
Imports System.IO

Public Class MainUI

    Dim PrimaryFolder As String
    Dim ShortCutType As String
    Private Sub Button2_Click(sender As Object, e As EventArgs) Handles Button2.Click
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
            ConfigTextBox.Text += "--stream_language " & StreamLanguage.Text & " "
        Else
            ConfigTextBox.Text += "--language " & StreamLanguage.Text & " "
        End If

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
        ' save ConfigTextBox.Text to a tmp bat file in the primary folder then run it
        Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
        File.WriteAllText(tmpBatFile, ConfigTextBox.Text)
        Process.Start(tmpBatFile)
    End Sub

    Private Sub microphone_id_button_Click(sender As Object, e As EventArgs) Handles microphone_id_button.Click
        Try
            If MIC_RadioButton.Checked = True Then
                Dim TempCommand As String = "call " & PrimaryFolder & "\data_whisper\Scripts\activate.bat"" " & vbNewLine & "python """ & ScriptFileLocation.Text & """ --microphone_enabled true --list_microphones"
                Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
                File.WriteAllText(tmpBatFile, TempCommand)
                Process.Start(tmpBatFile)
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
End Class
