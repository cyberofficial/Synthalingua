Imports System.IO
Imports System.Diagnostics
Imports System.Threading

Public Class MainUI
    Private PrimaryFolder As String
    Private ShortCutType As String
    Private Shared appMutex As Mutex

    Public WordBlockListLocation As String = "blacklist.txt"

    Private Sub Button2_Click(sender As Object, e As EventArgs) Handles SearchForProgramBTN.Click
        If Label1.ForeColor = Color.Red Then
            Label1.ForeColor = Color.Black
        End If

        Dim result = OpenScriptDiag.ShowDialog

        If result = DialogResult.Cancel Then
            MessageBox.Show("Action Canceled")
            Return
        End If

        ScriptFileLocation.Text = OpenScriptDiag.FileName
        PrimaryFolder = Path.GetDirectoryName(OpenScriptDiag.FileName)

        ShortCutType = If(Path.GetExtension(OpenScriptDiag.FileName) = ".py", "Source", "Portable")
    End Sub

    Private Sub ChunkSizeTrackBar_ValueChanged(sender As Object, e As EventArgs) Handles ChunkSizeTrackBar.ValueChanged
        ChunkSizeTrackBarValue.Text = "Chunks: " & ChunkSizeTrackBar.Value
    End Sub

    <Obsolete>
    Private Sub GenerateConfigButton_Click(sender As Object, e As EventArgs) Handles GenerateConfigButton.Click
        If String.IsNullOrEmpty(ScriptFileLocation.Text) Then
            MessageBox.Show("Please select the program file.")
            Exit Sub
        End If
        If String.IsNullOrEmpty(StreamLanguage.Text) Then
            MessageBox.Show("No Stream language was set.")
            Exit Sub
        End If

        ShortCutType = If(ScriptFileLocation.Text.Contains("transcribe_audio.py"), "Source", "Portable")
        PrimaryFolder = Path.GetDirectoryName(ScriptFileLocation.Text)

        Dim config As New Text.StringBuilder
        ' Basic setup
        config.AppendLine().AppendLine("cls").AppendLine("@echo off").AppendLine("Echo Loading Script")
        config.AppendLine($"""{PrimaryFolder}\set_up_env.exe""")
        config.AppendLine($"call ""{PrimaryFolder}\ffmpeg_path.bat""")

        ' Script execution command
        If ShortCutType = "Source" Then
            config.AppendLine($"call ""{PrimaryFolder}\data_whisper\Scripts\activate.bat""")
            config.Append($"python ""{PrimaryFolder}\transcribe_audio.py"" ")
        Else
            config.Append($"""{PrimaryFolder}\transcribe_audio.exe"" ")
        End If

        ' RAM settings
        config.Append($"--ram {RamSize.Text} ")
        If ForceRam.Checked Then config.Append("--ramforce ")

        ' Audio source specific settings
        If CAP_RadioButton.Checked Then
            config.Append($"--makecaptions --file_input=""{CaptionsInput.Text}"" --file_output=""{CaptionsOutput.Text}"" --file_output_name=""{CaptionsName.Text}"" ")
        ElseIf MIC_RadioButton.Checked Then
            config.Append("--microphone_enabled true ")
            If MicEnCheckBox.Checked Then config.Append($"--energy_threshold {EnThreshValue.Value} ")
            If MicCaliCheckBox.Checked Then config.Append($"--mic_calibration_time {MicCaliTime.Value} ")
            If RecordTimeOutCHeckBox.Checked Then config.Append($"--record_timeout {RecordTimeout.Value} ")
            If PhraseTimeOutCheckbox.Checked Then config.Append($"--phrase_timeout {PhraseTimeout.Value} ")
            config.Append($"--set_microphone {MicID.Value} ")
        ElseIf HSL_RadioButton.Checked Then
            If ShowOriginalText.Checked Then config.Append("--stream_original_text ")
            config.Append($"--stream ""{HLS_URL.Text}"" ")
            config.Append($"--stream_chunks {ChunkSizeTrackBar.Value} ")
        End If

        ' Language settings
        Dim prefix = If(HSL_RadioButton.Checked, "stream_", "")
        If StreamLanguage.Text <> "--Auto Detect--" Then
            config.Append($"--{prefix}language {StreamLanguage.Text} ")
        End If

        ' Translation settings
        If EnglishTranslationCheckBox.Checked Then
            config.Append($"--{prefix}translate ")
        End If
        If SecondaryTranslation.Checked Then
            config.Append($"--{prefix}transcribe ")
            config.Append($"--{prefix}target_language {SecondaryTranslationLanguage.Text} ")
        End If

        ' Device settings
        If CUDA_RadioButton.Checked Then
            config.Append("--device cuda ")
        ElseIf CPU_RadioButton.Checked Then
            config.Append("--device cpu ")
        End If

        ' Additional settings
        If Not String.IsNullOrEmpty(CookiesName.Text) Then config.Append($"--cookies {CookiesName.Text} ")
        If WordBlockList.Checked Then config.Append($"--ignorelist ""{WordBlockListLocation}"" ")
        If WebServerButton.Checked Then config.Append($"--portnumber {PortNumber.Value} ")
        If RepeatProtection.Checked Then config.Append("--condition_on_previous_text ")
        If cb_halspassword.Checked Then config.Append($"--remote_hls_password_id {hlspassid.Text} --remote_hls_password {hlspassword.Text} ")
        If Not String.IsNullOrEmpty(DiscordWebHook.Text) Then config.Append($"--discord_webhook ""{DiscordWebHook.Text}"" ")
        If Not String.IsNullOrEmpty(modelDIr.Text) Then config.Append($"--model_dir ""{modelDIr.Text}"" ")
        If PrecisionCheckBox.Checked Then config.Append("--fp16")

        config.AppendLine().AppendLine("pause")
        ConfigTextBox.Text = config.ToString()

    End Sub

    Private Sub SaveConfigToFileButton_Click(sender As Object, e As EventArgs) Handles SaveConfigToFileButton.Click
        SaveFileDialog.Filter = "Batch File|*.bat"
        SaveFileDialog.Title = "Save Config File"
        Dim unused = SaveFileDialog.ShowDialog
        If SaveFileDialog.FileName <> "" Then
            My.Computer.FileSystem.WriteAllText(SaveFileDialog.FileName, ConfigTextBox.Text, False)
        End If
    End Sub
    Private Sub RunScript_Click(sender As Object, e As EventArgs) Handles RunScript.Click
        If ScriptFileLocation.Text = "" Then
            Dim unused1 = MsgBox("Please select the program file.")
            Exit Sub
        End If
        If ConfigTextBox.Text = "" Then
            MessageBox.Show("Click generate first.")
        End If
        If CAP_RadioButton.Checked = True Then
            If CaptionsName.Text = "" Then
                Dim unused1 = MsgBox("Please set a file name for captions.")
                Exit Sub
            End If
            If CaptionsOutput.Text = "" Then
                Dim unused1 = MsgBox("Please set the output folder.")
                Exit Sub
            End If
            If CaptionsInput.Text = "" Then
                Dim unused1 = MsgBox("Please set the input file.")
                Exit Sub
            End If
        End If

        Try
            If My.Settings.PrimaryFolder IsNot Nothing AndAlso My.Settings.PrimaryFolder <> "" Then
                PrimaryFolder = My.Settings.PrimaryFolder
            End If
        Catch ex As Exception
        End Try
        If PrimaryFolder = "" Then
            MessageBox.Show("Primary folder is not set.")
            Exit Sub
        End If
        Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
        File.WriteAllText(tmpBatFile, ConfigTextBox.Text)
        Dim unused = Process.Start(tmpBatFile)
    End Sub

    Private Sub microphone_id_button_Click(sender As Object, e As EventArgs) Handles microphone_id_button.Click
        If Not MIC_RadioButton.Checked Then
            MessageBox.Show("Please select the microphone option")
            Return
        End If

        If String.IsNullOrEmpty(ScriptFileLocation.Text) Then
            MessageBox.Show("Please select the program file.")
            Return
        End If

        If ScriptFileLocation.Text.Contains(" ") Then
            MessageBox.Show("Please select a program file that does not have spaces in the file path.")
            Return
        End If

        Try
            Dim tmpBatFile As String = Path.Combine(PrimaryFolder, "tmp.bat")
            Dim TempCommand As String

            If ScriptFileLocation.Text.Contains(".py") Then
                TempCommand = $"call ""{PrimaryFolder}\data_whisper\Scripts\activate.bat"" {vbCrLf}python ""{ScriptFileLocation.Text}"" --microphone_enabled true --list_microphones"
            Else
                MessageBox.Show($"Running command: {ScriptFileLocation.Text} --microphone_enabled true --list_microphones")
                TempCommand = $"""{ScriptFileLocation.Text}"" --microphone_enabled true --list_microphones{vbCrLf}pause"
            End If

            File.WriteAllText(tmpBatFile, TempCommand)
            Process.Start(tmpBatFile)

        Catch ex As Exception
            MessageBox.Show($"Error: {ex.Message}{vbCrLf}Make sure the program path is valid and all required files are present.")
        End Try
    End Sub

    Private Sub CopyWebLink(linkType As String)
        Dim url As String = $"http://localhost:{PortNumber.Value}?show{linkType}"
        Clipboard.SetText(url)
        MessageBox.Show($"Copied {url} to clipboard")
    End Sub

    Private Sub WebLinkOG_Click(sender As Object, e As EventArgs) Handles WebLinkOG.Click
        CopyWebLink("original")
    End Sub

    Private Sub WebLinkT1_Click(sender As Object, e As EventArgs) Handles WebLinkT1.Click
        CopyWebLink("translation")
    End Sub

    Private Sub WebLinkT2_Click(sender As Object, e As EventArgs) Handles WebLinkT2.Click
        CopyWebLink("transcription")
    End Sub
    Private Sub MainUI_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        Me.Text = Me.Text & " v" & My.Application.Info.Version.ToString()

        Dim createdNew As Boolean
        appMutex = New Mutex(True, "Synthalingua_Wrapper", createdNew)
        With My.Settings
            If String.IsNullOrEmpty(.MainScriptLocation) Then
                ' Nag user
                'Dim unused = MsgBox("Could not find MainScriptLocation in settings. Please click the ""..."" to search for it.")
            Else
                ScriptFileLocation.Text = .MainScriptLocation
            End If

            HSL_RadioButton.Checked = (.AudioSource = 1)
            MIC_RadioButton.Checked = (.AudioSource = 2)
            CAP_RadioButton.Checked = (.AudioSource = 3)

            CUDA_RadioButton.Checked = (.ProcDevice = 1)
            CPU_RadioButton.Checked = Not (.ProcDevice = 1)

            PortNumber.Value = .WebServerPort
            WebServerButton.Checked = .WebServerEnabled
            RamSize.Text = .RamSize
            ForceRam.Checked = .ForceRam
            CookiesName.Text = .CookieName
            StreamLanguage.Text = .StreamLanguage
            EnglishTranslationCheckBox.Checked = .EnglishTranslationEnabled
            SecondaryTranslationLanguage.Text = .SecondaryTranslationLang
            SecondaryTranslation.Checked = .SecondaryTranslationEnabled
            HLS_URL.Text = .HLSurl
            ChunkSizeTrackBar.Value = .StreamChunkSize
            ShowOriginalText.Checked = .HLSShowOriginal
            EnThreshValue.Value = .MicrophoneEnergyThreshold
            MicEnCheckBox.Checked = .MicrophoneEnergyThresholdEnabled
            MicCaliTime.Value = .MicCalTime
            MicCaliCheckBox.Checked = .MicCalTImeEnabled
            RecordTimeout.Value = .MicRecTimeout
            RecordTimeOutCHeckBox.Checked = .MicRecTimeoutEnabled
            PhraseTimeout.Value = .PhraseTimeOut
            PhraseTimeOutCheckbox.Checked = .PhraseTimeOutEnabled
            WordBlockListLocation = .WordBlockListLocation
            WordBlockList.Checked = .WordBlockListEnabled
            RepeatProtection.Checked = .RepeatProtection
            ConfigTextBox.Text = .CommandBlock
            ShortCutType = .ShortCutType
            hlspassid.Text = .hlspassid
            hlspassword.Text = .hlspassword
            cb_halspassword.Checked = .cb_halspassword
            modelDIr.Text = .modelDIr
            PrecisionCheckBox.Checked = .fp16
            Try
                PrimaryFolder = .PrimaryFolder
            Catch ex As Exception
                PrimaryFolder = ""
            End Try
        End With

        Dim currentDirectory As String = System.IO.Directory.GetCurrentDirectory()

        Dim cookiesFolderPath As String = System.IO.Path.Combine(currentDirectory, "cookies")
        If Not System.IO.Directory.Exists(cookiesFolderPath) Then
            Dim unused1 = System.IO.Directory.CreateDirectory(cookiesFolderPath)
        End If

        If Directory.Exists(cookiesFolderPath) Then
            For Each file As String In Directory.GetFiles(cookiesFolderPath)
                Dim unused = CookiesName.Items.Add(Path.GetFileNameWithoutExtension(file))
            Next
        End If

        If String.IsNullOrEmpty(ScriptFileLocation.Text) Then
            Dim scriptFilePath As String = System.IO.Path.Combine(currentDirectory, "transcribe_audio.exe")
            If System.IO.File.Exists(scriptFilePath) Then
                ScriptFileLocation.Text = scriptFilePath
                PrimaryFolder = System.IO.Path.GetDirectoryName(scriptFilePath)
                ShortCutType = "Portable"
            Else
                scriptFilePath = System.IO.Path.Combine(currentDirectory, "transcribe_audio.py")
                If System.IO.File.Exists(scriptFilePath) Then
                    ScriptFileLocation.Text = scriptFilePath
                    PrimaryFolder = System.IO.Path.GetDirectoryName(scriptFilePath)
                    ShortCutType = "Source"
                End If
            End If
        End If

        If Not createdNew Then
            MessageBox.Show("This application is already running. Please change the port number if you plan to use multiple instances.", "Instance Already Running", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Return
        End If

    End Sub


    Private Sub CookiesRefresh_Click(sender As Object, e As EventArgs) Handles CookiesRefresh.Click
        CookiesName.Items.Clear()
        If Directory.Exists(Path.Combine(Application.StartupPath, "cookies")) Then
            For Each file As String In Directory.GetFiles(Path.Combine(Application.StartupPath, "cookies"))
                Dim unused = CookiesName.Items.Add(Path.GetFileNameWithoutExtension(file))
            Next
        End If
    End Sub

    Private Sub CookiesRefresh_MouseHover(sender As Object, e As EventArgs) Handles CookiesRefresh.MouseHover
        ToolTip1.SetToolTip(CookiesRefresh, "Clear the set cookie.")
    End Sub

    Private Sub Button2_MouseHover(sender As Object, e As EventArgs) Handles SearchForProgramBTN.MouseHover, CaptionsInputBtn.MouseHover, CaptionsOutputBtn.MouseHover
        ToolTip1.SetToolTip(SearchForProgramBTN, "Select the program file.")
    End Sub

    Private Sub SetWebLinkToolTip(control As Control, linkType As String)
        ToolTip1.SetToolTip(control, $"Copy the link to the clipboard. Will copy http://localhost:{PortNumber.Value}?show{linkType}")
    End Sub

    Private Sub WebLinkOG_MouseHover(sender As Object, e As EventArgs) Handles WebLinkOG.MouseHover
        SetWebLinkToolTip(WebLinkOG, "original")
    End Sub

    Private Sub WebLinkT1_MouseHover(sender As Object, e As EventArgs) Handles WebLinkT1.MouseHover
        SetWebLinkToolTip(WebLinkT1, "translation")
    End Sub

    Private Sub WebLinkT2_MouseHover(sender As Object, e As EventArgs) Handles WebLinkT2.MouseHover
        SetWebLinkToolTip(WebLinkT2, "transcription")
    End Sub

    Private Sub CheckBoxCMDBLock_CheckedChanged(sender As Object, e As EventArgs) Handles CheckBoxCMDBLock.CheckedChanged
        ConfigTextBox.Visible = CheckBoxCMDBLock.Checked <> False
    End Sub

    Private Sub HSL_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles HSL_RadioButton.MouseHover
        ToolTip1.SetToolTip(HSL_RadioButton, "Use HLS stream instead of microphone. HLS stream is a stream of audio from a website.")
    End Sub

    Private Sub MIC_RadioButton_MouseHover(sender As Object, e As EventArgs) Handles MIC_RadioButton.MouseHover, CAP_RadioButton.MouseHover
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
        Dim unused = MessageBox.Show("Set the energy threshold. This is the amount of energy required to start recording. The higher the number the more energy is required to start recording.")
    End Sub

    Private Sub MicCaliLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles MicCaliLbl.MouseClick
        Dim unused = MessageBox.Show("Set the microphone calibration time. This is the amount of time to calibrate the microphone. The higher the number the more time it will take to calibrate the microphone.")
    End Sub

    Private Sub RecordTimeoutLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles RecordTimeoutLbl.MouseClick
        Dim unused = MessageBox.Show("Set the record timeout. This is the amount of time to record for. The higher the number the more time it will record for.")
    End Sub

    Private Sub PhraseTimeOutlbl_MouseClick(sender As Object, e As MouseEventArgs) Handles PhraseTimeOutlbl.MouseClick
        Dim unused = MessageBox.Show("Set the phrase timeout. This is the amount of time to wait for a phrase. The higher the number the more time it will wait for a phrase. How many sentences in a paragraph it'll show.")
    End Sub

    Private Sub SetMicLbl_MouseClick(sender As Object, e As MouseEventArgs) Handles SetMicLbl.MouseClick
        Dim unused = MessageBox.Show("Set the microphone to use, click Get IDs and set the ID of the microphone.")
    End Sub

    Private Sub SubWindow_Click(sender As Object, e As EventArgs) Handles SubWindow.Click
        If WebServerButton.Checked = True Then
            subtitlewindow.Show()
        Else
            Dim unused = MessageBox.Show("Please enable the web server to use this feature.")
        End If
    End Sub

    Private Sub CaptionsInputBtn_Click(sender As Object, e As EventArgs) Handles CaptionsInputBtn.Click
        Dim unused = CaptionsInputFile.ShowDialog
        CaptionsInput.Text = CaptionsInputFile.FileName
        CaptionsName.Text = Path.GetFileNameWithoutExtension(CaptionsInputFile.SafeFileName)
    End Sub

    Private Sub CaptionsOutputBtn_Click(sender As Object, e As EventArgs) Handles CaptionsOutputBtn.Click
        Dim unused = FolderBrowserDialog1.ShowDialog
        CaptionsOutput.Text = FolderBrowserDialog1.SelectedPath
    End Sub

    Private Sub SaveConfig_Click(sender As Object, e As EventArgs) Handles SaveConfig.Click
        With My.Settings
            ' Script Location
            .MainScriptLocation = ScriptFileLocation.Text

            ' Audio Source
            .AudioSource = If(HSL_RadioButton.Checked, 1, If(MIC_RadioButton.Checked, 2, 3))

            ' Processor Device
            .ProcDevice = If(CUDA_RadioButton.Checked, 1, 2)

            ' Web Server
            .WebServerEnabled = If(WebServerButton.Checked, 1, 0)
            .WebServerPort = PortNumber.Value

            ' RAM Size
            .RamSize = RamSize.Text

            ' Model Location
            .modelDIr = modelDIr.Text

            ' Force RAM
            .ForceRam = ForceRam.Checked

            ' Cookie Name
            .CookieName = CookiesName.Text

            ' Stream Language
            .StreamLanguage = StreamLanguage.Text

            ' English Translation
            .EnglishTranslationEnabled = EnglishTranslationCheckBox.Checked

            ' Secondary Translation
            .SecondaryTranslationLang = SecondaryTranslationLanguage.Text
            .SecondaryTranslationEnabled = SecondaryTranslation.Checked

            ' HLS URL
            .HLSurl = HLS_URL.Text

            ' Stream Chunk Size
            .StreamChunkSize = ChunkSizeTrackBar.Value

            ' Show Original Text
            .HLSShowOriginal = ShowOriginalText.Checked

            ' Microphone Energy Threshold
            .MicrophoneEnergyThreshold = EnThreshValue.Value
            .MicrophoneEnergyThresholdEnabled = MicEnCheckBox.Checked

            ' Microphone Calibration Time
            .MicCalTime = MicCaliTime.Value
            .MicCalTImeEnabled = MicCaliCheckBox.Checked

            ' Microphone Record Timeout
            .MicRecTimeout = RecordTimeout.Value
            .MicRecTimeoutEnabled = RecordTimeOutCHeckBox.Checked

            ' Phrase Timeout
            .PhraseTimeOut = PhraseTimeout.Value
            .PhraseTimeOutEnabled = PhraseTimeOutCheckbox.Checked

            ' Word Block List
            .WordBlockListEnabled = WordBlockList.Checked
            .WordBlockListLocation = WordBlockListLocation.ToString

            ' Repeat Protection
            .RepeatProtection = RepeatProtection.Checked

            ' Command Block
            .PrimaryFolder = PrimaryFolder
            .ShortCutType = ShortCutType
            .CommandBlock = ConfigTextBox.Text

            'hls info
            .hlspassid = hlspassid.Text
            .hlspassword = hlspassword.Text
            .cb_halspassword = cb_halspassword.Checked

            'Precision Mode
            .fp16 = PrecisionCheckBox.Checked

        End With
        My.Settings.Save()
    End Sub


    Private Sub WipeSettings_Click(sender As Object, e As EventArgs) Handles WipeSettings.Click
        Dim confirmResult As DialogResult = MessageBox.Show("Are you sure you want to wipe all settings? This will reset all application settings and close the application.", "Confirm Wipe", MessageBoxButtons.YesNo, MessageBoxIcon.Information)
        If confirmResult = DialogResult.Yes Then
            If EraseCheckBox.Checked Then
                Dim warningResult As DialogResult = MessageBox.Show("This action will clear all settings and close the application. Are you really sure?", "Warning", MessageBoxButtons.YesNo, MessageBoxIcon.Warning)
                If warningResult = DialogResult.Yes Then
                    My.Settings.Reset()
                    My.Settings.Save()
                    Dim finalResult As DialogResult = MessageBox.Show("All settings have been cleared. Application will close now.", "Settings Cleared", MessageBoxButtons.OK, MessageBoxIcon.Information)

                    If finalResult = DialogResult.OK Then
                        Application.Exit()
                    End If
                Else
                    EraseCheckBox.Checked = False
                End If
            Else
                MessageBox.Show("If you want to clear settings, click the checkbox first.", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            End If
        End If
    End Sub

    Private Sub EditBlockList_Click(sender As Object, e As EventArgs) Handles EditBlockList.Click
        Try
            Dim directoryPath As String = System.IO.Path.GetDirectoryName(ScriptFileLocation.Text)
            Dim filePath As String = System.IO.Path.Combine(WordBlockListLocation)
            If Not System.IO.File.Exists(filePath) Then
                Try
                    System.IO.File.Create(filePath).Close()
                Catch ex As Exception
                    MessageBox.Show("An error occurred while creating the file: " & ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End Try
            End If
            Try
                System.Diagnostics.Process.Start("notepad.exe", filePath)
            Catch ex As Exception
                MessageBox.Show("An error occurred while opening the file: " & ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            End Try
        Catch ex As Exception
            MessageBox.Show(ex.ToString)
        End Try
    End Sub

    Private Sub RepeatProtection_MouseHover(sender As Object, e As EventArgs) Handles RepeatProtection.MouseHover
        ToolTip1.SetToolTip(RepeatProtection, "Will help the model from repeating itself, but may slow up the process.")
    End Sub
    Private Sub Button1_Click(sender As Object, e As EventArgs) Handles Button1.Click
        Dim OpenFileDiag As New OpenFileDialog With {
            .Filter = "Text File (*.txt)|*.txt",
            .Title = "Load a Word Block list."
        }
        OpenFileDiag.ShowDialog()
        If OpenFileDiag.FileName = "" Then
            MessageBox.Show("Word list not set", "Nothing was set.")
            Exit Sub
        End If
        WordBlockListLocation = OpenFileDiag.FileName
        MessageBox.Show($"Loaded: {WordBlockListLocation}")
    End Sub

    Private Sub Button3_Click(sender As Object, e As EventArgs) Handles Button3.Click
        WebBrowserConfig.ShowDialog()
    End Sub

    Private Sub cb_halspassword_CheckedChanged(sender As Object, e As EventArgs) Handles cb_halspassword.CheckedChanged
        If cb_halspassword.Checked Then
            HLS_URL.PasswordChar = "*"
        Else
            HLS_URL.PasswordChar = ""
        End If
    End Sub
    Private Sub OpenSocialLink(url As String)
        Process.Start(New ProcessStartInfo(url) With {.UseShellExecute = True})
    End Sub

    Private Sub PictureItch_MouseClick(sender As Object, e As MouseEventArgs) Handles PictureItch.MouseClick
        OpenSocialLink("https://cyberofficial.itch.io/synthalingua")
    End Sub

    Private Sub GitHubPicture_MouseClick(sender As Object, e As MouseEventArgs) Handles GitHubPicture.MouseClick
        OpenSocialLink("https://github.com/cyberofficial/Synthalingua")
    End Sub

    Private Sub KoFiPicture_MouseClick(sender As Object, e As MouseEventArgs) Handles KoFiPicture.MouseClick
        OpenSocialLink("https://ko-fi.com/cyberofficial")
    End Sub
    Private Sub modelDirPicker_Click(sender As Object, e As EventArgs) Handles modelDirPicker.Click
        Using folderBrowserDialog As New FolderBrowserDialog()
            If folderBrowserDialog.ShowDialog() = DialogResult.OK Then
                modelDIr.Text = folderBrowserDialog.SelectedPath
            End If
        End Using
    End Sub
End Class
