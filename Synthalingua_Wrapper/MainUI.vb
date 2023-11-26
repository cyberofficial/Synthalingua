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
        If MIC_RadioButton.Checked = True Then
            Dim TempCommand As String = "call " & PrimaryFolder & "\data_whisper\Scripts\activate.bat"" " & vbNewLine & "python """ & ScriptFileLocation.Text & """ --microphone_enabled true --list_microphones"
            MessageBox.Show(TempCommand)
            Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
            File.WriteAllText(tmpBatFile, TempCommand)
            Process.Start(tmpBatFile)
        Else
            MsgBox("Please select the microphone option")

        End If
    End Sub
End Class
