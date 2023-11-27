<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()>
Partial Class MainUI
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()>
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
    <System.Diagnostics.DebuggerStepThrough()>
    Private Sub InitializeComponent()
        components = New ComponentModel.Container()
        GroupBox1 = New GroupBox()
        MIC_RadioButton = New RadioButton()
        HSL_RadioButton = New RadioButton()
        SaveConfigToFileButton = New Button()
        Label1 = New Label()
        ScriptFileLocation = New TextBox()
        Button2 = New Button()
        Label2 = New Label()
        RamSize = New ComboBox()
        ForceRam = New CheckBox()
        GroupBox2 = New GroupBox()
        ShowOriginalText = New CheckBox()
        ChunkSizeTrackBarValue = New Label()
        ChunkSizeTrackBar = New TrackBar()
        Label6 = New Label()
        HLS_URL = New TextBox()
        Label3 = New Label()
        EnglishTranslationCheckBox = New CheckBox()
        Label7 = New Label()
        SecondaryTranslation = New CheckBox()
        Label5 = New Label()
        SecondaryTranslationLanguage = New ComboBox()
        StreamLanguage = New ComboBox()
        Label4 = New Label()
        GroupBox3 = New GroupBox()
        CPU_RadioButton = New RadioButton()
        CUDA_RadioButton = New RadioButton()
        OpenScriptDiag = New OpenFileDialog()
        ConfigTextBox = New TextBox()
        GenerateConfigButton = New Button()
        Label8 = New Label()
        SaveFileDialog = New SaveFileDialog()
        PortNumber = New NumericUpDown()
        WebServerButton = New CheckBox()
        Label10 = New Label()
        GroupBox4 = New GroupBox()
        TabControl1 = New TabControl()
        TabPage1 = New TabPage()
        TabPage2 = New TabPage()
        PhraseTimeOutCheckbox = New CheckBox()
        RecordTimeOutCHeckBox = New CheckBox()
        MicCaliCheckBox = New CheckBox()
        MicEnCheckBox = New CheckBox()
        microphone_id_button = New Button()
        Label14 = New Label()
        MicID = New NumericUpDown()
        PhraseTimeout = New NumericUpDown()
        RecordTimeout = New NumericUpDown()
        MicCaliTime = New NumericUpDown()
        Label12 = New Label()
        EnThreshValue = New NumericUpDown()
        Label11 = New Label()
        Label9 = New Label()
        Energy_Threshold = New Label()
        MicIDs = New Button()
        RunScript = New Button()
        Label13 = New Label()
        DiscordWebHook = New TextBox()
        GroupBox5 = New GroupBox()
        WebLinkT2 = New Button()
        WebLinkT1 = New Button()
        WebLinkOG = New Button()
        Label15 = New Label()
        CookiesName = New ComboBox()
        CookiesRefresh = New Button()
        ToolTip1 = New ToolTip(components)
        GroupBox1.SuspendLayout()
        GroupBox2.SuspendLayout()
        CType(ChunkSizeTrackBar, ComponentModel.ISupportInitialize).BeginInit()
        GroupBox3.SuspendLayout()
        CType(PortNumber, ComponentModel.ISupportInitialize).BeginInit()
        GroupBox4.SuspendLayout()
        TabControl1.SuspendLayout()
        TabPage1.SuspendLayout()
        TabPage2.SuspendLayout()
        CType(MicID, ComponentModel.ISupportInitialize).BeginInit()
        CType(PhraseTimeout, ComponentModel.ISupportInitialize).BeginInit()
        CType(RecordTimeout, ComponentModel.ISupportInitialize).BeginInit()
        CType(MicCaliTime, ComponentModel.ISupportInitialize).BeginInit()
        CType(EnThreshValue, ComponentModel.ISupportInitialize).BeginInit()
        GroupBox5.SuspendLayout()
        SuspendLayout()
        ' 
        ' GroupBox1
        ' 
        GroupBox1.Controls.Add(MIC_RadioButton)
        GroupBox1.Controls.Add(HSL_RadioButton)
        GroupBox1.Location = New Point(12, 12)
        GroupBox1.Name = "GroupBox1"
        GroupBox1.Size = New Size(157, 95)
        GroupBox1.TabIndex = 0
        GroupBox1.TabStop = False
        GroupBox1.Text = "Audio Soruce"
        ' 
        ' MIC_RadioButton
        ' 
        MIC_RadioButton.AutoSize = True
        MIC_RadioButton.Location = New Point(6, 56)
        MIC_RadioButton.Name = "MIC_RadioButton"
        MIC_RadioButton.Size = New Size(110, 24)
        MIC_RadioButton.TabIndex = 1
        MIC_RadioButton.TabStop = True
        MIC_RadioButton.Text = "Microphone"
        MIC_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' HSL_RadioButton
        ' 
        HSL_RadioButton.AutoSize = True
        HSL_RadioButton.Checked = True
        HSL_RadioButton.Location = New Point(6, 26)
        HSL_RadioButton.Name = "HSL_RadioButton"
        HSL_RadioButton.Size = New Size(107, 24)
        HSL_RadioButton.TabIndex = 0
        HSL_RadioButton.TabStop = True
        HSL_RadioButton.Text = "HLS Stream"
        HSL_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' SaveConfigToFileButton
        ' 
        SaveConfigToFileButton.Font = New Font("Segoe UI", 12F)
        SaveConfigToFileButton.Location = New Point(586, 844)
        SaveConfigToFileButton.Name = "SaveConfigToFileButton"
        SaveConfigToFileButton.Size = New Size(123, 42)
        SaveConfigToFileButton.TabIndex = 1
        SaveConfigToFileButton.Text = "Save to File"
        SaveConfigToFileButton.UseVisualStyleBackColor = True
        ' 
        ' Label1
        ' 
        Label1.AutoSize = True
        Label1.Location = New Point(175, 12)
        Label1.Name = "Label1"
        Label1.Size = New Size(188, 20)
        Label1.TabIndex = 2
        Label1.Text = "Script or Portable Location:"
        ' 
        ' ScriptFileLocation
        ' 
        ScriptFileLocation.Location = New Point(369, 9)
        ScriptFileLocation.Name = "ScriptFileLocation"
        ScriptFileLocation.PlaceholderText = "C:\Somelocation"
        ScriptFileLocation.Size = New Size(292, 27)
        ScriptFileLocation.TabIndex = 3
        ' 
        ' Button2
        ' 
        Button2.Location = New Point(669, 8)
        Button2.Name = "Button2"
        Button2.Size = New Size(40, 29)
        Button2.TabIndex = 4
        Button2.Text = "..."
        Button2.UseVisualStyleBackColor = True
        ' 
        ' Label2
        ' 
        Label2.AutoSize = True
        Label2.Location = New Point(175, 57)
        Label2.Name = "Label2"
        Label2.Size = New Size(75, 20)
        Label2.TabIndex = 5
        Label2.Text = "RAM Size:"
        ' 
        ' RamSize
        ' 
        RamSize.AutoCompleteMode = AutoCompleteMode.Append
        RamSize.AutoCompleteSource = AutoCompleteSource.ListItems
        RamSize.DropDownStyle = ComboBoxStyle.DropDownList
        RamSize.FormattingEnabled = True
        RamSize.Items.AddRange(New Object() {"1gb", "2gb", "4gb", "6gb", "12gb"})
        RamSize.Location = New Point(256, 54)
        RamSize.Name = "RamSize"
        RamSize.Size = New Size(82, 28)
        RamSize.TabIndex = 6
        ' 
        ' ForceRam
        ' 
        ForceRam.AutoSize = True
        ForceRam.Location = New Point(344, 56)
        ForceRam.Name = "ForceRam"
        ForceRam.Size = New Size(101, 24)
        ForceRam.TabIndex = 7
        ForceRam.Text = "Force Ram"
        ForceRam.UseVisualStyleBackColor = True
        ' 
        ' GroupBox2
        ' 
        GroupBox2.Controls.Add(ShowOriginalText)
        GroupBox2.Controls.Add(ChunkSizeTrackBarValue)
        GroupBox2.Controls.Add(ChunkSizeTrackBar)
        GroupBox2.Controls.Add(Label6)
        GroupBox2.Controls.Add(HLS_URL)
        GroupBox2.Controls.Add(Label3)
        GroupBox2.Location = New Point(6, 12)
        GroupBox2.Name = "GroupBox2"
        GroupBox2.Size = New Size(514, 133)
        GroupBox2.TabIndex = 8
        GroupBox2.TabStop = False
        GroupBox2.Text = "HLS Info"
        ' 
        ' ShowOriginalText
        ' 
        ShowOriginalText.AutoSize = True
        ShowOriginalText.Location = New Point(6, 94)
        ShowOriginalText.Name = "ShowOriginalText"
        ShowOriginalText.Size = New Size(155, 24)
        ShowOriginalText.TabIndex = 23
        ShowOriginalText.Text = "Show Original Text"
        ShowOriginalText.UseVisualStyleBackColor = True
        ' 
        ' ChunkSizeTrackBarValue
        ' 
        ChunkSizeTrackBarValue.AutoSize = True
        ChunkSizeTrackBarValue.Location = New Point(146, 62)
        ChunkSizeTrackBarValue.Name = "ChunkSizeTrackBarValue"
        ChunkSizeTrackBarValue.Size = New Size(70, 20)
        ChunkSizeTrackBarValue.TabIndex = 11
        ChunkSizeTrackBarValue.Text = "Chunks: 5"
        ' 
        ' ChunkSizeTrackBar
        ' 
        ChunkSizeTrackBar.Location = New Point(222, 62)
        ChunkSizeTrackBar.Maximum = 30
        ChunkSizeTrackBar.Minimum = 1
        ChunkSizeTrackBar.Name = "ChunkSizeTrackBar"
        ChunkSizeTrackBar.Size = New Size(286, 56)
        ChunkSizeTrackBar.TabIndex = 10
        ChunkSizeTrackBar.Value = 5
        ' 
        ' Label6
        ' 
        Label6.AutoSize = True
        Label6.Location = New Point(6, 62)
        Label6.Name = "Label6"
        Label6.Size = New Size(134, 20)
        Label6.TabIndex = 9
        Label6.Text = "Stream Chunk Size:"
        ' 
        ' HLS_URL
        ' 
        HLS_URL.Location = New Point(101, 20)
        HLS_URL.Name = "HLS_URL"
        HLS_URL.PlaceholderText = "Stream URL"
        HLS_URL.Size = New Size(407, 27)
        HLS_URL.TabIndex = 1
        ' 
        ' Label3
        ' 
        Label3.AutoSize = True
        Label3.Location = New Point(6, 23)
        Label3.Name = "Label3"
        Label3.Size = New Size(89, 20)
        Label3.TabIndex = 0
        Label3.Text = "Stream URL:"
        ' 
        ' EnglishTranslationCheckBox
        ' 
        EnglishTranslationCheckBox.AutoSize = True
        EnglishTranslationCheckBox.Location = New Point(316, 121)
        EnglishTranslationCheckBox.Name = "EnglishTranslationCheckBox"
        EnglishTranslationCheckBox.Size = New Size(278, 24)
        EnglishTranslationCheckBox.TabIndex = 8
        EnglishTranslationCheckBox.Text = "Enable | Will also do regular captions"
        EnglishTranslationCheckBox.UseVisualStyleBackColor = True
        ' 
        ' Label7
        ' 
        Label7.AutoSize = True
        Label7.Location = New Point(175, 122)
        Label7.Name = "Label7"
        Label7.Size = New Size(135, 20)
        Label7.TabIndex = 7
        Label7.Text = "English Translation:"
        ' 
        ' SecondaryTranslation
        ' 
        SecondaryTranslation.AutoSize = True
        SecondaryTranslation.Location = New Point(528, 150)
        SecondaryTranslation.Name = "SecondaryTranslation"
        SecondaryTranslation.Size = New Size(149, 24)
        SecondaryTranslation.TabIndex = 5
        SecondaryTranslation.Text = "Enable Secondary"
        SecondaryTranslation.UseVisualStyleBackColor = True
        ' 
        ' Label5
        ' 
        Label5.AutoSize = True
        Label5.Location = New Point(175, 151)
        Label5.Name = "Label5"
        Label5.Size = New Size(157, 20)
        Label5.TabIndex = 4
        Label5.Text = "Secondary Translation:"
        ' 
        ' SecondaryTranslationLanguage
        ' 
        SecondaryTranslationLanguage.DisplayMember = "1"
        SecondaryTranslationLanguage.DropDownStyle = ComboBoxStyle.DropDownList
        SecondaryTranslationLanguage.FormattingEnabled = True
        SecondaryTranslationLanguage.Items.AddRange(New Object() {"Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"})
        SecondaryTranslationLanguage.Location = New Point(338, 148)
        SecondaryTranslationLanguage.Name = "SecondaryTranslationLanguage"
        SecondaryTranslationLanguage.Size = New Size(184, 28)
        SecondaryTranslationLanguage.Sorted = True
        SecondaryTranslationLanguage.TabIndex = 3
        ' 
        ' StreamLanguage
        ' 
        StreamLanguage.DisplayMember = "1"
        StreamLanguage.DropDownStyle = ComboBoxStyle.DropDownList
        StreamLanguage.FormattingEnabled = True
        StreamLanguage.Items.AddRange(New Object() {"Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"})
        StreamLanguage.Location = New Point(313, 87)
        StreamLanguage.Name = "StreamLanguage"
        StreamLanguage.Size = New Size(396, 28)
        StreamLanguage.Sorted = True
        StreamLanguage.TabIndex = 3
        ' 
        ' Label4
        ' 
        Label4.AutoSize = True
        Label4.Location = New Point(175, 90)
        Label4.Name = "Label4"
        Label4.Size = New Size(132, 20)
        Label4.TabIndex = 2
        Label4.Text = "Stream Language: "
        ' 
        ' GroupBox3
        ' 
        GroupBox3.Controls.Add(CPU_RadioButton)
        GroupBox3.Controls.Add(CUDA_RadioButton)
        GroupBox3.Location = New Point(12, 113)
        GroupBox3.Name = "GroupBox3"
        GroupBox3.Size = New Size(157, 93)
        GroupBox3.TabIndex = 9
        GroupBox3.TabStop = False
        GroupBox3.Text = "Proc Device"
        ' 
        ' CPU_RadioButton
        ' 
        CPU_RadioButton.AutoSize = True
        CPU_RadioButton.Location = New Point(6, 56)
        CPU_RadioButton.Name = "CPU_RadioButton"
        CPU_RadioButton.Size = New Size(54, 24)
        CPU_RadioButton.TabIndex = 0
        CPU_RadioButton.Text = "cpu"
        CPU_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' CUDA_RadioButton
        ' 
        CUDA_RadioButton.AutoSize = True
        CUDA_RadioButton.Checked = True
        CUDA_RadioButton.Location = New Point(6, 26)
        CUDA_RadioButton.Name = "CUDA_RadioButton"
        CUDA_RadioButton.Size = New Size(62, 24)
        CUDA_RadioButton.TabIndex = 0
        CUDA_RadioButton.TabStop = True
        CUDA_RadioButton.Text = "cuda"
        CUDA_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' OpenScriptDiag
        ' 
        OpenScriptDiag.FileName = "transcribe_audio.exe"
        OpenScriptDiag.Filter = "EXE (*.exe)|*.exe|py Files (*.py)|*.py"
        ' 
        ' ConfigTextBox
        ' 
        ConfigTextBox.Font = New Font("Segoe UI", 13F)
        ConfigTextBox.Location = New Point(175, 444)
        ConfigTextBox.Multiline = True
        ConfigTextBox.Name = "ConfigTextBox"
        ConfigTextBox.ReadOnly = True
        ConfigTextBox.ScrollBars = ScrollBars.Vertical
        ConfigTextBox.Size = New Size(534, 394)
        ConfigTextBox.TabIndex = 10
        ' 
        ' GenerateConfigButton
        ' 
        GenerateConfigButton.Font = New Font("Segoe UI", 13F)
        GenerateConfigButton.Location = New Point(175, 844)
        GenerateConfigButton.Name = "GenerateConfigButton"
        GenerateConfigButton.Size = New Size(132, 42)
        GenerateConfigButton.TabIndex = 11
        GenerateConfigButton.Text = "Generate Config"
        GenerateConfigButton.UseVisualStyleBackColor = True
        ' 
        ' Label8
        ' 
        Label8.AutoSize = True
        Label8.Location = New Point(451, 57)
        Label8.Name = "Label8"
        Label8.Size = New Size(129, 20)
        Label8.TabIndex = 12
        Label8.Text = "Cookie File Name:"
        ' 
        ' PortNumber
        ' 
        PortNumber.Location = New Point(7, 69)
        PortNumber.Maximum = New Decimal(New Integer() {65535, 0, 0, 0})
        PortNumber.Name = "PortNumber"
        PortNumber.Size = New Size(95, 27)
        PortNumber.TabIndex = 15
        PortNumber.Value = New Decimal(New Integer() {2000, 0, 0, 0})
        ' 
        ' WebServerButton
        ' 
        WebServerButton.AutoSize = True
        WebServerButton.Location = New Point(6, 19)
        WebServerButton.Name = "WebServerButton"
        WebServerButton.Size = New Size(76, 24)
        WebServerButton.TabIndex = 16
        WebServerButton.Text = "Enable"
        WebServerButton.UseVisualStyleBackColor = True
        ' 
        ' Label10
        ' 
        Label10.AutoSize = True
        Label10.Location = New Point(6, 46)
        Label10.Name = "Label10"
        Label10.Size = New Size(96, 20)
        Label10.TabIndex = 17
        Label10.Text = "Port Number:"
        ' 
        ' GroupBox4
        ' 
        GroupBox4.Controls.Add(Label10)
        GroupBox4.Controls.Add(PortNumber)
        GroupBox4.Controls.Add(WebServerButton)
        GroupBox4.Location = New Point(12, 212)
        GroupBox4.Name = "GroupBox4"
        GroupBox4.Size = New Size(157, 109)
        GroupBox4.TabIndex = 18
        GroupBox4.TabStop = False
        GroupBox4.Text = "Web Server"
        ' 
        ' TabControl1
        ' 
        TabControl1.Controls.Add(TabPage1)
        TabControl1.Controls.Add(TabPage2)
        TabControl1.Location = New Point(175, 235)
        TabControl1.Name = "TabControl1"
        TabControl1.SelectedIndex = 0
        TabControl1.Size = New Size(534, 203)
        TabControl1.TabIndex = 19
        ' 
        ' TabPage1
        ' 
        TabPage1.Controls.Add(GroupBox2)
        TabPage1.Location = New Point(4, 29)
        TabPage1.Name = "TabPage1"
        TabPage1.Padding = New Padding(3)
        TabPage1.Size = New Size(526, 170)
        TabPage1.TabIndex = 0
        TabPage1.Text = "HLS Settings"
        TabPage1.UseVisualStyleBackColor = True
        ' 
        ' TabPage2
        ' 
        TabPage2.Controls.Add(PhraseTimeOutCheckbox)
        TabPage2.Controls.Add(RecordTimeOutCHeckBox)
        TabPage2.Controls.Add(MicCaliCheckBox)
        TabPage2.Controls.Add(MicEnCheckBox)
        TabPage2.Controls.Add(microphone_id_button)
        TabPage2.Controls.Add(Label14)
        TabPage2.Controls.Add(MicID)
        TabPage2.Controls.Add(PhraseTimeout)
        TabPage2.Controls.Add(RecordTimeout)
        TabPage2.Controls.Add(MicCaliTime)
        TabPage2.Controls.Add(Label12)
        TabPage2.Controls.Add(EnThreshValue)
        TabPage2.Controls.Add(Label11)
        TabPage2.Controls.Add(Label9)
        TabPage2.Controls.Add(Energy_Threshold)
        TabPage2.Location = New Point(4, 29)
        TabPage2.Name = "TabPage2"
        TabPage2.Padding = New Padding(3)
        TabPage2.Size = New Size(526, 170)
        TabPage2.TabIndex = 1
        TabPage2.Text = "Microphone Settings"
        TabPage2.UseVisualStyleBackColor = True
        ' 
        ' PhraseTimeOutCheckbox
        ' 
        PhraseTimeOutCheckbox.AutoSize = True
        PhraseTimeOutCheckbox.Location = New Point(308, 104)
        PhraseTimeOutCheckbox.Name = "PhraseTimeOutCheckbox"
        PhraseTimeOutCheckbox.Size = New Size(76, 24)
        PhraseTimeOutCheckbox.TabIndex = 24
        PhraseTimeOutCheckbox.Text = "Enable"
        PhraseTimeOutCheckbox.UseVisualStyleBackColor = True
        ' 
        ' RecordTimeOutCHeckBox
        ' 
        RecordTimeOutCHeckBox.AutoSize = True
        RecordTimeOutCHeckBox.Location = New Point(308, 71)
        RecordTimeOutCHeckBox.Name = "RecordTimeOutCHeckBox"
        RecordTimeOutCHeckBox.Size = New Size(76, 24)
        RecordTimeOutCHeckBox.TabIndex = 24
        RecordTimeOutCHeckBox.Text = "Enable"
        RecordTimeOutCHeckBox.UseVisualStyleBackColor = True
        ' 
        ' MicCaliCheckBox
        ' 
        MicCaliCheckBox.AutoSize = True
        MicCaliCheckBox.Location = New Point(308, 38)
        MicCaliCheckBox.Name = "MicCaliCheckBox"
        MicCaliCheckBox.Size = New Size(76, 24)
        MicCaliCheckBox.TabIndex = 24
        MicCaliCheckBox.Text = "Enable"
        MicCaliCheckBox.UseVisualStyleBackColor = True
        ' 
        ' MicEnCheckBox
        ' 
        MicEnCheckBox.AutoSize = True
        MicEnCheckBox.Location = New Point(308, 5)
        MicEnCheckBox.Name = "MicEnCheckBox"
        MicEnCheckBox.Size = New Size(76, 24)
        MicEnCheckBox.TabIndex = 24
        MicEnCheckBox.Text = "Enable"
        MicEnCheckBox.UseVisualStyleBackColor = True
        ' 
        ' microphone_id_button
        ' 
        microphone_id_button.Location = New Point(308, 131)
        microphone_id_button.Name = "microphone_id_button"
        microphone_id_button.Size = New Size(94, 29)
        microphone_id_button.TabIndex = 4
        microphone_id_button.Text = "Get IDs"
        microphone_id_button.UseVisualStyleBackColor = True
        ' 
        ' Label14
        ' 
        Label14.AutoSize = True
        Label14.Location = New Point(92, 135)
        Label14.Name = "Label14"
        Label14.Size = New Size(117, 20)
        Label14.TabIndex = 3
        Label14.Text = "Set Microphone:"
        ' 
        ' MicID
        ' 
        MicID.Location = New Point(215, 133)
        MicID.Maximum = New Decimal(New Integer() {9999, 0, 0, 0})
        MicID.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        MicID.Name = "MicID"
        MicID.Size = New Size(87, 27)
        MicID.TabIndex = 2
        MicID.Value = New Decimal(New Integer() {1, 0, 0, 0})
        ' 
        ' PhraseTimeout
        ' 
        PhraseTimeout.Location = New Point(215, 103)
        PhraseTimeout.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        PhraseTimeout.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        PhraseTimeout.Name = "PhraseTimeout"
        PhraseTimeout.Size = New Size(87, 27)
        PhraseTimeout.TabIndex = 2
        PhraseTimeout.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' RecordTimeout
        ' 
        RecordTimeout.Location = New Point(215, 70)
        RecordTimeout.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        RecordTimeout.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        RecordTimeout.Name = "RecordTimeout"
        RecordTimeout.Size = New Size(87, 27)
        RecordTimeout.TabIndex = 2
        RecordTimeout.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' MicCaliTime
        ' 
        MicCaliTime.Location = New Point(215, 37)
        MicCaliTime.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        MicCaliTime.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        MicCaliTime.Name = "MicCaliTime"
        MicCaliTime.Size = New Size(87, 27)
        MicCaliTime.TabIndex = 2
        MicCaliTime.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' Label12
        ' 
        Label12.AutoSize = True
        Label12.Location = New Point(98, 105)
        Label12.Name = "Label12"
        Label12.Size = New Size(111, 20)
        Label12.TabIndex = 1
        Label12.Text = "Phrase Timeout"
        ' 
        ' EnThreshValue
        ' 
        EnThreshValue.Location = New Point(215, 4)
        EnThreshValue.Maximum = New Decimal(New Integer() {1000, 0, 0, 0})
        EnThreshValue.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        EnThreshValue.Name = "EnThreshValue"
        EnThreshValue.Size = New Size(87, 27)
        EnThreshValue.TabIndex = 2
        EnThreshValue.Value = New Decimal(New Integer() {1, 0, 0, 0})
        ' 
        ' Label11
        ' 
        Label11.AutoSize = True
        Label11.Location = New Point(94, 72)
        Label11.Name = "Label11"
        Label11.Size = New Size(115, 20)
        Label11.TabIndex = 1
        Label11.Text = "Record Timeout"
        ' 
        ' Label9
        ' 
        Label9.AutoSize = True
        Label9.Location = New Point(6, 39)
        Label9.Name = "Label9"
        Label9.Size = New Size(203, 20)
        Label9.TabIndex = 1
        Label9.Text = "Microphone Calibration Time"
        ' 
        ' Energy_Threshold
        ' 
        Energy_Threshold.AutoSize = True
        Energy_Threshold.Location = New Point(6, 6)
        Energy_Threshold.Name = "Energy_Threshold"
        Energy_Threshold.Size = New Size(123, 20)
        Energy_Threshold.TabIndex = 1
        Energy_Threshold.Text = "Energy Threshold"
        ' 
        ' MicIDs
        ' 
        MicIDs.Location = New Point(308, 131)
        MicIDs.Name = "MicIDs"
        MicIDs.Size = New Size(94, 29)
        MicIDs.TabIndex = 4
        MicIDs.Text = "Get IDs"
        MicIDs.UseVisualStyleBackColor = True
        ' 
        ' RunScript
        ' 
        RunScript.Font = New Font("Segoe UI", 15F)
        RunScript.Location = New Point(313, 844)
        RunScript.Name = "RunScript"
        RunScript.Size = New Size(268, 42)
        RunScript.TabIndex = 20
        RunScript.Text = "Run"
        RunScript.UseVisualStyleBackColor = True
        ' 
        ' Label13
        ' 
        Label13.AutoSize = True
        Label13.Location = New Point(175, 212)
        Label13.Name = "Label13"
        Label13.Size = New Size(141, 20)
        Label13.TabIndex = 21
        Label13.Text = "Discord Web Hook: "
        ' 
        ' DiscordWebHook
        ' 
        DiscordWebHook.Location = New Point(313, 209)
        DiscordWebHook.Name = "DiscordWebHook"
        DiscordWebHook.PasswordChar = "*"c
        DiscordWebHook.PlaceholderText = "<--- Discord WebHook URL --->"
        DiscordWebHook.Size = New Size(396, 27)
        DiscordWebHook.TabIndex = 22
        ' 
        ' GroupBox5
        ' 
        GroupBox5.Controls.Add(WebLinkT2)
        GroupBox5.Controls.Add(WebLinkT1)
        GroupBox5.Controls.Add(WebLinkOG)
        GroupBox5.Controls.Add(Label15)
        GroupBox5.Location = New Point(12, 327)
        GroupBox5.Name = "GroupBox5"
        GroupBox5.Size = New Size(157, 151)
        GroupBox5.TabIndex = 25
        GroupBox5.TabStop = False
        GroupBox5.Text = "Browser Source"
        ' 
        ' WebLinkT2
        ' 
        WebLinkT2.Location = New Point(6, 113)
        WebLinkT2.Name = "WebLinkT2"
        WebLinkT2.Size = New Size(145, 29)
        WebLinkT2.TabIndex = 1
        WebLinkT2.Text = "Translation 2"
        WebLinkT2.UseVisualStyleBackColor = True
        ' 
        ' WebLinkT1
        ' 
        WebLinkT1.Location = New Point(6, 78)
        WebLinkT1.Name = "WebLinkT1"
        WebLinkT1.Size = New Size(145, 29)
        WebLinkT1.TabIndex = 1
        WebLinkT1.Text = "Translation"
        WebLinkT1.UseVisualStyleBackColor = True
        ' 
        ' WebLinkOG
        ' 
        WebLinkOG.Location = New Point(6, 46)
        WebLinkOG.Name = "WebLinkOG"
        WebLinkOG.Size = New Size(145, 29)
        WebLinkOG.TabIndex = 1
        WebLinkOG.Text = "Original Text"
        WebLinkOG.UseVisualStyleBackColor = True
        ' 
        ' Label15
        ' 
        Label15.AutoSize = True
        Label15.Location = New Point(6, 23)
        Label15.Name = "Label15"
        Label15.Size = New Size(96, 20)
        Label15.TabIndex = 0
        Label15.Text = "Click to Copy"
        ' 
        ' CookiesName
        ' 
        CookiesName.AutoCompleteMode = AutoCompleteMode.SuggestAppend
        CookiesName.AutoCompleteSource = AutoCompleteSource.ListItems
        CookiesName.DropDownStyle = ComboBoxStyle.DropDownList
        CookiesName.FormattingEnabled = True
        CookiesName.Location = New Point(579, 54)
        CookiesName.Name = "CookiesName"
        CookiesName.Size = New Size(98, 28)
        CookiesName.TabIndex = 26
        ' 
        ' CookiesRefresh
        ' 
        CookiesRefresh.FlatStyle = FlatStyle.Flat
        CookiesRefresh.Font = New Font("Segoe UI", 8F)
        CookiesRefresh.ImageAlign = ContentAlignment.TopLeft
        CookiesRefresh.Location = New Point(684, 54)
        CookiesRefresh.Name = "CookiesRefresh"
        CookiesRefresh.Size = New Size(25, 28)
        CookiesRefresh.TabIndex = 27
        CookiesRefresh.Text = "🔃"
        CookiesRefresh.UseVisualStyleBackColor = True
        ' 
        ' MainUI
        ' 
        AutoScaleDimensions = New SizeF(8F, 20F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(713, 898)
        Controls.Add(CookiesRefresh)
        Controls.Add(CookiesName)
        Controls.Add(GroupBox5)
        Controls.Add(DiscordWebHook)
        Controls.Add(Label13)
        Controls.Add(RunScript)
        Controls.Add(TabControl1)
        Controls.Add(GroupBox4)
        Controls.Add(EnglishTranslationCheckBox)
        Controls.Add(Label8)
        Controls.Add(Label7)
        Controls.Add(GenerateConfigButton)
        Controls.Add(SecondaryTranslation)
        Controls.Add(ConfigTextBox)
        Controls.Add(Label5)
        Controls.Add(GroupBox3)
        Controls.Add(SecondaryTranslationLanguage)
        Controls.Add(ForceRam)
        Controls.Add(StreamLanguage)
        Controls.Add(RamSize)
        Controls.Add(Label4)
        Controls.Add(Label2)
        Controls.Add(Button2)
        Controls.Add(ScriptFileLocation)
        Controls.Add(Label1)
        Controls.Add(SaveConfigToFileButton)
        Controls.Add(GroupBox1)
        FormBorderStyle = FormBorderStyle.FixedSingle
        MaximizeBox = False
        Name = "MainUI"
        StartPosition = FormStartPosition.CenterScreen
        Text = "Synthalingua - Shortcut Maker"
        GroupBox1.ResumeLayout(False)
        GroupBox1.PerformLayout()
        GroupBox2.ResumeLayout(False)
        GroupBox2.PerformLayout()
        CType(ChunkSizeTrackBar, ComponentModel.ISupportInitialize).EndInit()
        GroupBox3.ResumeLayout(False)
        GroupBox3.PerformLayout()
        CType(PortNumber, ComponentModel.ISupportInitialize).EndInit()
        GroupBox4.ResumeLayout(False)
        GroupBox4.PerformLayout()
        TabControl1.ResumeLayout(False)
        TabPage1.ResumeLayout(False)
        TabPage2.ResumeLayout(False)
        TabPage2.PerformLayout()
        CType(MicID, ComponentModel.ISupportInitialize).EndInit()
        CType(PhraseTimeout, ComponentModel.ISupportInitialize).EndInit()
        CType(RecordTimeout, ComponentModel.ISupportInitialize).EndInit()
        CType(MicCaliTime, ComponentModel.ISupportInitialize).EndInit()
        CType(EnThreshValue, ComponentModel.ISupportInitialize).EndInit()
        GroupBox5.ResumeLayout(False)
        GroupBox5.PerformLayout()
        ResumeLayout(False)
        PerformLayout()
    End Sub

    Friend WithEvents GroupBox1 As GroupBox
    Friend WithEvents MIC_RadioButton As RadioButton
    Friend WithEvents HSL_RadioButton As RadioButton
    Friend WithEvents SaveConfigToFileButton As Button
    Friend WithEvents Label1 As Label
    Friend WithEvents ScriptFileLocation As TextBox
    Friend WithEvents Button2 As Button
    Friend WithEvents Label2 As Label
    Friend WithEvents RamSize As ComboBox
    Friend WithEvents ForceRam As CheckBox
    Friend WithEvents GroupBox2 As GroupBox
    Friend WithEvents HLS_URL As TextBox
    Friend WithEvents Label3 As Label
    Friend WithEvents GroupBox3 As GroupBox
    Friend WithEvents CPU_RadioButton As RadioButton
    Friend WithEvents CUDA_RadioButton As RadioButton
    Friend WithEvents StreamLanguage As ComboBox
    Friend WithEvents Label4 As Label
    Friend WithEvents Label5 As Label
    Friend WithEvents SecondaryTranslationLanguage As ComboBox
    Friend WithEvents SecondaryTranslation As CheckBox
    Friend WithEvents Label7 As Label
    Friend WithEvents EnglishTranslationCheckBox As CheckBox
    Friend WithEvents ChunkSizeTrackBar As TrackBar
    Friend WithEvents Label6 As Label
    Friend WithEvents ChunkSizeTrackBarValue As Label
    Friend WithEvents OpenScriptDiag As OpenFileDialog
    Friend WithEvents ConfigTextBox As TextBox
    Friend WithEvents GenerateConfigButton As Button
    Friend WithEvents Label8 As Label
    Friend WithEvents SaveFileDialog As SaveFileDialog
    Friend WithEvents PortNumber As NumericUpDown
    Friend WithEvents WebServerButton As CheckBox
    Friend WithEvents Label10 As Label
    Friend WithEvents GroupBox4 As GroupBox
    Friend WithEvents TabControl1 As TabControl
    Friend WithEvents TabPage1 As TabPage
    Friend WithEvents TabPage2 As TabPage
    Friend WithEvents RunScript As Button
    Friend WithEvents Energy_Threshold As Label
    Friend WithEvents PhraseTimeout As NumericUpDown
    Friend WithEvents RecordTimeout As NumericUpDown
    Friend WithEvents MicCaliTime As NumericUpDown
    Friend WithEvents Label12 As Label
    Friend WithEvents EnThreshValue As NumericUpDown
    Friend WithEvents Label11 As Label
    Friend WithEvents Label9 As Label
    Friend WithEvents Label13 As Label
    Friend WithEvents DiscordWebHook As TextBox
    Friend WithEvents Label14 As Label
    Friend WithEvents MicID As NumericUpDown
    Friend WithEvents MicIDs As Button
    Friend WithEvents microphone_id_button As Button
    Friend WithEvents PhraseTimeOutCheckbox As CheckBox
    Friend WithEvents RecordTimeOutCHeckBox As CheckBox
    Friend WithEvents MicCaliCheckBox As CheckBox
    Friend WithEvents MicEnCheckBox As CheckBox
    Friend WithEvents ShowOriginalText As CheckBox
    Friend WithEvents GroupBox5 As GroupBox
    Friend WithEvents WebLinkT1 As Button
    Friend WithEvents WebLinkOG As Button
    Friend WithEvents Label15 As Label
    Friend WithEvents WebLinkT2 As Button
    Friend WithEvents CookiesName As ComboBox
    Friend WithEvents CookiesRefresh As Button
    Friend WithEvents ToolTip1 As ToolTip

End Class
