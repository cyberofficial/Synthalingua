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
        SetMicLbl = New Label()
        MicID = New NumericUpDown()
        PhraseTimeout = New NumericUpDown()
        RecordTimeout = New NumericUpDown()
        MicCaliTime = New NumericUpDown()
        PhraseTimeOutlbl = New Label()
        EnThreshValue = New NumericUpDown()
        RecordTimeoutLbl = New Label()
        MicCaliLbl = New Label()
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
        CheckBoxCMDBLock = New CheckBox()
        SubWindow = New Button()
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
        GroupBox1.Location = New Point(10, 9)
        GroupBox1.Margin = New Padding(3, 2, 3, 2)
        GroupBox1.Name = "GroupBox1"
        GroupBox1.Padding = New Padding(3, 2, 3, 2)
        GroupBox1.Size = New Size(137, 71)
        GroupBox1.TabIndex = 0
        GroupBox1.TabStop = False
        GroupBox1.Text = "Audio Soruce"
        ' 
        ' MIC_RadioButton
        ' 
        MIC_RadioButton.AutoSize = True
        MIC_RadioButton.Location = New Point(5, 42)
        MIC_RadioButton.Margin = New Padding(3, 2, 3, 2)
        MIC_RadioButton.Name = "MIC_RadioButton"
        MIC_RadioButton.Size = New Size(90, 19)
        MIC_RadioButton.TabIndex = 1
        MIC_RadioButton.TabStop = True
        MIC_RadioButton.Text = "Microphone"
        MIC_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' HSL_RadioButton
        ' 
        HSL_RadioButton.AutoSize = True
        HSL_RadioButton.Checked = True
        HSL_RadioButton.Location = New Point(5, 20)
        HSL_RadioButton.Margin = New Padding(3, 2, 3, 2)
        HSL_RadioButton.Name = "HSL_RadioButton"
        HSL_RadioButton.Size = New Size(86, 19)
        HSL_RadioButton.TabIndex = 0
        HSL_RadioButton.TabStop = True
        HSL_RadioButton.Text = "HLS Stream"
        HSL_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' SaveConfigToFileButton
        ' 
        SaveConfigToFileButton.Font = New Font("Segoe UI", 12F)
        SaveConfigToFileButton.Location = New Point(513, 633)
        SaveConfigToFileButton.Margin = New Padding(3, 2, 3, 2)
        SaveConfigToFileButton.Name = "SaveConfigToFileButton"
        SaveConfigToFileButton.Size = New Size(108, 32)
        SaveConfigToFileButton.TabIndex = 1
        SaveConfigToFileButton.Text = "Save to File"
        SaveConfigToFileButton.UseVisualStyleBackColor = True
        ' 
        ' Label1
        ' 
        Label1.AutoSize = True
        Label1.Location = New Point(153, 9)
        Label1.Name = "Label1"
        Label1.Size = New Size(150, 15)
        Label1.TabIndex = 2
        Label1.Text = "Script or Portable Location:"
        ' 
        ' ScriptFileLocation
        ' 
        ScriptFileLocation.Location = New Point(323, 7)
        ScriptFileLocation.Margin = New Padding(3, 2, 3, 2)
        ScriptFileLocation.Name = "ScriptFileLocation"
        ScriptFileLocation.PlaceholderText = "C:\Somelocation"
        ScriptFileLocation.Size = New Size(256, 23)
        ScriptFileLocation.TabIndex = 3
        ' 
        ' Button2
        ' 
        Button2.Location = New Point(585, 6)
        Button2.Margin = New Padding(3, 2, 3, 2)
        Button2.Name = "Button2"
        Button2.Size = New Size(35, 22)
        Button2.TabIndex = 4
        Button2.Text = "..."
        Button2.UseVisualStyleBackColor = True
        ' 
        ' Label2
        ' 
        Label2.AutoSize = True
        Label2.Location = New Point(153, 43)
        Label2.Name = "Label2"
        Label2.Size = New Size(59, 15)
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
        RamSize.Location = New Point(224, 40)
        RamSize.Margin = New Padding(3, 2, 3, 2)
        RamSize.Name = "RamSize"
        RamSize.Size = New Size(72, 23)
        RamSize.TabIndex = 6
        ' 
        ' ForceRam
        ' 
        ForceRam.AutoSize = True
        ForceRam.Location = New Point(301, 42)
        ForceRam.Margin = New Padding(3, 2, 3, 2)
        ForceRam.Name = "ForceRam"
        ForceRam.Size = New Size(82, 19)
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
        GroupBox2.Location = New Point(5, 9)
        GroupBox2.Margin = New Padding(3, 2, 3, 2)
        GroupBox2.Name = "GroupBox2"
        GroupBox2.Padding = New Padding(3, 2, 3, 2)
        GroupBox2.Size = New Size(450, 100)
        GroupBox2.TabIndex = 8
        GroupBox2.TabStop = False
        GroupBox2.Text = "HLS Info"
        ' 
        ' ShowOriginalText
        ' 
        ShowOriginalText.AutoSize = True
        ShowOriginalText.Location = New Point(5, 70)
        ShowOriginalText.Margin = New Padding(3, 2, 3, 2)
        ShowOriginalText.Name = "ShowOriginalText"
        ShowOriginalText.Size = New Size(124, 19)
        ShowOriginalText.TabIndex = 23
        ShowOriginalText.Text = "Show Original Text"
        ShowOriginalText.UseVisualStyleBackColor = True
        ' 
        ' ChunkSizeTrackBarValue
        ' 
        ChunkSizeTrackBarValue.AutoSize = True
        ChunkSizeTrackBarValue.Location = New Point(128, 46)
        ChunkSizeTrackBarValue.Name = "ChunkSizeTrackBarValue"
        ChunkSizeTrackBarValue.Size = New Size(59, 15)
        ChunkSizeTrackBarValue.TabIndex = 11
        ChunkSizeTrackBarValue.Text = "Chunks: 5"
        ' 
        ' ChunkSizeTrackBar
        ' 
        ChunkSizeTrackBar.Location = New Point(194, 46)
        ChunkSizeTrackBar.Margin = New Padding(3, 2, 3, 2)
        ChunkSizeTrackBar.Maximum = 30
        ChunkSizeTrackBar.Minimum = 1
        ChunkSizeTrackBar.Name = "ChunkSizeTrackBar"
        ChunkSizeTrackBar.Size = New Size(250, 45)
        ChunkSizeTrackBar.TabIndex = 10
        ChunkSizeTrackBar.Value = 5
        ' 
        ' Label6
        ' 
        Label6.AutoSize = True
        Label6.Location = New Point(5, 46)
        Label6.Name = "Label6"
        Label6.Size = New Size(108, 15)
        Label6.TabIndex = 9
        Label6.Text = "Stream Chunk Size:"
        ' 
        ' HLS_URL
        ' 
        HLS_URL.Location = New Point(88, 15)
        HLS_URL.Margin = New Padding(3, 2, 3, 2)
        HLS_URL.Name = "HLS_URL"
        HLS_URL.PlaceholderText = "Stream URL"
        HLS_URL.Size = New Size(357, 23)
        HLS_URL.TabIndex = 1
        ' 
        ' Label3
        ' 
        Label3.AutoSize = True
        Label3.Location = New Point(5, 17)
        Label3.Name = "Label3"
        Label3.Size = New Size(71, 15)
        Label3.TabIndex = 0
        Label3.Text = "Stream URL:"
        ' 
        ' EnglishTranslationCheckBox
        ' 
        EnglishTranslationCheckBox.AutoSize = True
        EnglishTranslationCheckBox.Location = New Point(276, 91)
        EnglishTranslationCheckBox.Margin = New Padding(3, 2, 3, 2)
        EnglishTranslationCheckBox.Name = "EnglishTranslationCheckBox"
        EnglishTranslationCheckBox.Size = New Size(219, 19)
        EnglishTranslationCheckBox.TabIndex = 8
        EnglishTranslationCheckBox.Text = "Enable | Will also do regular captions"
        EnglishTranslationCheckBox.UseVisualStyleBackColor = True
        ' 
        ' Label7
        ' 
        Label7.AutoSize = True
        Label7.Location = New Point(153, 92)
        Label7.Name = "Label7"
        Label7.Size = New Size(108, 15)
        Label7.TabIndex = 7
        Label7.Text = "English Translation:"
        ' 
        ' SecondaryTranslation
        ' 
        SecondaryTranslation.AutoSize = True
        SecondaryTranslation.Location = New Point(462, 112)
        SecondaryTranslation.Margin = New Padding(3, 2, 3, 2)
        SecondaryTranslation.Name = "SecondaryTranslation"
        SecondaryTranslation.Size = New Size(119, 19)
        SecondaryTranslation.TabIndex = 5
        SecondaryTranslation.Text = "Enable Secondary"
        SecondaryTranslation.UseVisualStyleBackColor = True
        ' 
        ' Label5
        ' 
        Label5.AutoSize = True
        Label5.Location = New Point(153, 113)
        Label5.Name = "Label5"
        Label5.Size = New Size(125, 15)
        Label5.TabIndex = 4
        Label5.Text = "Secondary Translation:"
        ' 
        ' SecondaryTranslationLanguage
        ' 
        SecondaryTranslationLanguage.DisplayMember = "1"
        SecondaryTranslationLanguage.DropDownStyle = ComboBoxStyle.DropDownList
        SecondaryTranslationLanguage.FormattingEnabled = True
        SecondaryTranslationLanguage.Items.AddRange(New Object() {"Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"})
        SecondaryTranslationLanguage.Location = New Point(296, 111)
        SecondaryTranslationLanguage.Margin = New Padding(3, 2, 3, 2)
        SecondaryTranslationLanguage.Name = "SecondaryTranslationLanguage"
        SecondaryTranslationLanguage.Size = New Size(162, 23)
        SecondaryTranslationLanguage.Sorted = True
        SecondaryTranslationLanguage.TabIndex = 3
        ' 
        ' StreamLanguage
        ' 
        StreamLanguage.DisplayMember = "1"
        StreamLanguage.DropDownStyle = ComboBoxStyle.DropDownList
        StreamLanguage.FormattingEnabled = True
        StreamLanguage.Items.AddRange(New Object() {"--Auto Detect--", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"})
        StreamLanguage.Location = New Point(274, 65)
        StreamLanguage.Margin = New Padding(3, 2, 3, 2)
        StreamLanguage.Name = "StreamLanguage"
        StreamLanguage.Size = New Size(347, 23)
        StreamLanguage.Sorted = True
        StreamLanguage.TabIndex = 3
        ' 
        ' Label4
        ' 
        Label4.AutoSize = True
        Label4.Location = New Point(153, 68)
        Label4.Name = "Label4"
        Label4.Size = New Size(105, 15)
        Label4.TabIndex = 2
        Label4.Text = "Stream Language: "
        ' 
        ' GroupBox3
        ' 
        GroupBox3.Controls.Add(CPU_RadioButton)
        GroupBox3.Controls.Add(CUDA_RadioButton)
        GroupBox3.Location = New Point(10, 85)
        GroupBox3.Margin = New Padding(3, 2, 3, 2)
        GroupBox3.Name = "GroupBox3"
        GroupBox3.Padding = New Padding(3, 2, 3, 2)
        GroupBox3.Size = New Size(137, 70)
        GroupBox3.TabIndex = 9
        GroupBox3.TabStop = False
        GroupBox3.Text = "Proc Device"
        ' 
        ' CPU_RadioButton
        ' 
        CPU_RadioButton.AutoSize = True
        CPU_RadioButton.Location = New Point(5, 42)
        CPU_RadioButton.Margin = New Padding(3, 2, 3, 2)
        CPU_RadioButton.Name = "CPU_RadioButton"
        CPU_RadioButton.Size = New Size(45, 19)
        CPU_RadioButton.TabIndex = 0
        CPU_RadioButton.Text = "cpu"
        CPU_RadioButton.UseVisualStyleBackColor = True
        ' 
        ' CUDA_RadioButton
        ' 
        CUDA_RadioButton.AutoSize = True
        CUDA_RadioButton.Checked = True
        CUDA_RadioButton.Location = New Point(5, 20)
        CUDA_RadioButton.Margin = New Padding(3, 2, 3, 2)
        CUDA_RadioButton.Name = "CUDA_RadioButton"
        CUDA_RadioButton.Size = New Size(51, 19)
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
        ConfigTextBox.Location = New Point(153, 350)
        ConfigTextBox.Margin = New Padding(3, 2, 3, 2)
        ConfigTextBox.Multiline = True
        ConfigTextBox.Name = "ConfigTextBox"
        ConfigTextBox.ReadOnly = True
        ConfigTextBox.ScrollBars = ScrollBars.Vertical
        ConfigTextBox.Size = New Size(468, 279)
        ConfigTextBox.TabIndex = 10
        ConfigTextBox.Visible = False
        ' 
        ' GenerateConfigButton
        ' 
        GenerateConfigButton.Font = New Font("Segoe UI", 13F)
        GenerateConfigButton.Location = New Point(153, 633)
        GenerateConfigButton.Margin = New Padding(3, 2, 3, 2)
        GenerateConfigButton.Name = "GenerateConfigButton"
        GenerateConfigButton.Size = New Size(116, 32)
        GenerateConfigButton.TabIndex = 11
        GenerateConfigButton.Text = "Generate Config"
        GenerateConfigButton.UseVisualStyleBackColor = True
        ' 
        ' Label8
        ' 
        Label8.AutoSize = True
        Label8.Location = New Point(395, 43)
        Label8.Name = "Label8"
        Label8.Size = New Size(103, 15)
        Label8.TabIndex = 12
        Label8.Text = "Cookie File Name:"
        ' 
        ' PortNumber
        ' 
        PortNumber.Location = New Point(6, 52)
        PortNumber.Margin = New Padding(3, 2, 3, 2)
        PortNumber.Maximum = New Decimal(New Integer() {65535, 0, 0, 0})
        PortNumber.Name = "PortNumber"
        PortNumber.Size = New Size(83, 23)
        PortNumber.TabIndex = 15
        PortNumber.Value = New Decimal(New Integer() {2000, 0, 0, 0})
        ' 
        ' WebServerButton
        ' 
        WebServerButton.AutoSize = True
        WebServerButton.Location = New Point(5, 14)
        WebServerButton.Margin = New Padding(3, 2, 3, 2)
        WebServerButton.Name = "WebServerButton"
        WebServerButton.Size = New Size(61, 19)
        WebServerButton.TabIndex = 16
        WebServerButton.Text = "Enable"
        WebServerButton.UseVisualStyleBackColor = True
        ' 
        ' Label10
        ' 
        Label10.AutoSize = True
        Label10.Location = New Point(5, 34)
        Label10.Name = "Label10"
        Label10.Size = New Size(79, 15)
        Label10.TabIndex = 17
        Label10.Text = "Port Number:"
        ' 
        ' GroupBox4
        ' 
        GroupBox4.Controls.Add(Label10)
        GroupBox4.Controls.Add(PortNumber)
        GroupBox4.Controls.Add(WebServerButton)
        GroupBox4.Location = New Point(10, 159)
        GroupBox4.Margin = New Padding(3, 2, 3, 2)
        GroupBox4.Name = "GroupBox4"
        GroupBox4.Padding = New Padding(3, 2, 3, 2)
        GroupBox4.Size = New Size(137, 82)
        GroupBox4.TabIndex = 18
        GroupBox4.TabStop = False
        GroupBox4.Text = "Web Server"
        ' 
        ' TabControl1
        ' 
        TabControl1.Controls.Add(TabPage1)
        TabControl1.Controls.Add(TabPage2)
        TabControl1.Location = New Point(153, 176)
        TabControl1.Margin = New Padding(3, 2, 3, 2)
        TabControl1.Name = "TabControl1"
        TabControl1.SelectedIndex = 0
        TabControl1.Size = New Size(467, 152)
        TabControl1.TabIndex = 19
        ' 
        ' TabPage1
        ' 
        TabPage1.Controls.Add(GroupBox2)
        TabPage1.Location = New Point(4, 24)
        TabPage1.Margin = New Padding(3, 2, 3, 2)
        TabPage1.Name = "TabPage1"
        TabPage1.Padding = New Padding(3, 2, 3, 2)
        TabPage1.Size = New Size(459, 124)
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
        TabPage2.Controls.Add(SetMicLbl)
        TabPage2.Controls.Add(MicID)
        TabPage2.Controls.Add(PhraseTimeout)
        TabPage2.Controls.Add(RecordTimeout)
        TabPage2.Controls.Add(MicCaliTime)
        TabPage2.Controls.Add(PhraseTimeOutlbl)
        TabPage2.Controls.Add(EnThreshValue)
        TabPage2.Controls.Add(RecordTimeoutLbl)
        TabPage2.Controls.Add(MicCaliLbl)
        TabPage2.Controls.Add(Energy_Threshold)
        TabPage2.Location = New Point(4, 24)
        TabPage2.Margin = New Padding(3, 2, 3, 2)
        TabPage2.Name = "TabPage2"
        TabPage2.Padding = New Padding(3, 2, 3, 2)
        TabPage2.Size = New Size(459, 124)
        TabPage2.TabIndex = 1
        TabPage2.Text = "Microphone Settings"
        TabPage2.UseVisualStyleBackColor = True
        ' 
        ' PhraseTimeOutCheckbox
        ' 
        PhraseTimeOutCheckbox.AutoSize = True
        PhraseTimeOutCheckbox.Location = New Point(287, 78)
        PhraseTimeOutCheckbox.Margin = New Padding(3, 2, 3, 2)
        PhraseTimeOutCheckbox.Name = "PhraseTimeOutCheckbox"
        PhraseTimeOutCheckbox.Size = New Size(61, 19)
        PhraseTimeOutCheckbox.TabIndex = 24
        PhraseTimeOutCheckbox.Text = "Enable"
        PhraseTimeOutCheckbox.UseVisualStyleBackColor = True
        ' 
        ' RecordTimeOutCHeckBox
        ' 
        RecordTimeOutCHeckBox.AutoSize = True
        RecordTimeOutCHeckBox.Location = New Point(287, 53)
        RecordTimeOutCHeckBox.Margin = New Padding(3, 2, 3, 2)
        RecordTimeOutCHeckBox.Name = "RecordTimeOutCHeckBox"
        RecordTimeOutCHeckBox.Size = New Size(61, 19)
        RecordTimeOutCHeckBox.TabIndex = 24
        RecordTimeOutCHeckBox.Text = "Enable"
        RecordTimeOutCHeckBox.UseVisualStyleBackColor = True
        ' 
        ' MicCaliCheckBox
        ' 
        MicCaliCheckBox.AutoSize = True
        MicCaliCheckBox.Location = New Point(287, 28)
        MicCaliCheckBox.Margin = New Padding(3, 2, 3, 2)
        MicCaliCheckBox.Name = "MicCaliCheckBox"
        MicCaliCheckBox.Size = New Size(61, 19)
        MicCaliCheckBox.TabIndex = 24
        MicCaliCheckBox.Text = "Enable"
        MicCaliCheckBox.UseVisualStyleBackColor = True
        ' 
        ' MicEnCheckBox
        ' 
        MicEnCheckBox.AutoSize = True
        MicEnCheckBox.Location = New Point(287, 4)
        MicEnCheckBox.Margin = New Padding(3, 2, 3, 2)
        MicEnCheckBox.Name = "MicEnCheckBox"
        MicEnCheckBox.Size = New Size(61, 19)
        MicEnCheckBox.TabIndex = 24
        MicEnCheckBox.Text = "Enable"
        MicEnCheckBox.UseVisualStyleBackColor = True
        ' 
        ' microphone_id_button
        ' 
        microphone_id_button.Location = New Point(287, 98)
        microphone_id_button.Margin = New Padding(3, 2, 3, 2)
        microphone_id_button.Name = "microphone_id_button"
        microphone_id_button.Size = New Size(82, 22)
        microphone_id_button.TabIndex = 4
        microphone_id_button.Text = "Get IDs"
        microphone_id_button.UseVisualStyleBackColor = True
        ' 
        ' SetMicLbl
        ' 
        SetMicLbl.AutoSize = True
        SetMicLbl.Location = New Point(86, 101)
        SetMicLbl.Name = "SetMicLbl"
        SetMicLbl.Size = New Size(110, 15)
        SetMicLbl.TabIndex = 3
        SetMicLbl.Text = "Set Microphone (?):"
        ' 
        ' MicID
        ' 
        MicID.Location = New Point(206, 100)
        MicID.Margin = New Padding(3, 2, 3, 2)
        MicID.Maximum = New Decimal(New Integer() {9999, 0, 0, 0})
        MicID.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        MicID.Name = "MicID"
        MicID.Size = New Size(76, 23)
        MicID.TabIndex = 2
        MicID.Value = New Decimal(New Integer() {1, 0, 0, 0})
        ' 
        ' PhraseTimeout
        ' 
        PhraseTimeout.Location = New Point(206, 77)
        PhraseTimeout.Margin = New Padding(3, 2, 3, 2)
        PhraseTimeout.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        PhraseTimeout.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        PhraseTimeout.Name = "PhraseTimeout"
        PhraseTimeout.Size = New Size(76, 23)
        PhraseTimeout.TabIndex = 2
        PhraseTimeout.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' RecordTimeout
        ' 
        RecordTimeout.Location = New Point(206, 52)
        RecordTimeout.Margin = New Padding(3, 2, 3, 2)
        RecordTimeout.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        RecordTimeout.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        RecordTimeout.Name = "RecordTimeout"
        RecordTimeout.Size = New Size(76, 23)
        RecordTimeout.TabIndex = 2
        RecordTimeout.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' MicCaliTime
        ' 
        MicCaliTime.Location = New Point(206, 28)
        MicCaliTime.Margin = New Padding(3, 2, 3, 2)
        MicCaliTime.Maximum = New Decimal(New Integer() {10, 0, 0, 0})
        MicCaliTime.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        MicCaliTime.Name = "MicCaliTime"
        MicCaliTime.Size = New Size(76, 23)
        MicCaliTime.TabIndex = 2
        MicCaliTime.Value = New Decimal(New Integer() {5, 0, 0, 0})
        ' 
        ' PhraseTimeOutlbl
        ' 
        PhraseTimeOutlbl.AutoSize = True
        PhraseTimeOutlbl.Location = New Point(86, 79)
        PhraseTimeOutlbl.Name = "PhraseTimeOutlbl"
        PhraseTimeOutlbl.Size = New Size(111, 15)
        PhraseTimeOutlbl.TabIndex = 1
        PhraseTimeOutlbl.Text = "Phrase Timeout (?): "
        ' 
        ' EnThreshValue
        ' 
        EnThreshValue.Location = New Point(206, 3)
        EnThreshValue.Margin = New Padding(3, 2, 3, 2)
        EnThreshValue.Maximum = New Decimal(New Integer() {1000, 0, 0, 0})
        EnThreshValue.Minimum = New Decimal(New Integer() {1, 0, 0, 0})
        EnThreshValue.Name = "EnThreshValue"
        EnThreshValue.Size = New Size(76, 23)
        EnThreshValue.TabIndex = 2
        EnThreshValue.Value = New Decimal(New Integer() {1, 0, 0, 0})
        ' 
        ' RecordTimeoutLbl
        ' 
        RecordTimeoutLbl.AutoSize = True
        RecordTimeoutLbl.Location = New Point(82, 54)
        RecordTimeoutLbl.Name = "RecordTimeoutLbl"
        RecordTimeoutLbl.Size = New Size(113, 15)
        RecordTimeoutLbl.TabIndex = 1
        RecordTimeoutLbl.Text = "Record Timeout (?): "
        ' 
        ' MicCaliLbl
        ' 
        MicCaliLbl.AutoSize = True
        MicCaliLbl.Location = New Point(5, 29)
        MicCaliLbl.Name = "MicCaliLbl"
        MicCaliLbl.Size = New Size(184, 15)
        MicCaliLbl.TabIndex = 1
        MicCaliLbl.Text = "Microphone Calibration Time (?): "
        ' 
        ' Energy_Threshold
        ' 
        Energy_Threshold.AutoSize = True
        Energy_Threshold.Location = New Point(75, 4)
        Energy_Threshold.Name = "Energy_Threshold"
        Energy_Threshold.Size = New Size(120, 15)
        Energy_Threshold.TabIndex = 1
        Energy_Threshold.Text = "Energy Threshold (?): "
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
        RunScript.Location = New Point(274, 633)
        RunScript.Margin = New Padding(3, 2, 3, 2)
        RunScript.Name = "RunScript"
        RunScript.Size = New Size(234, 32)
        RunScript.TabIndex = 20
        RunScript.Text = "Run"
        RunScript.UseVisualStyleBackColor = True
        ' 
        ' Label13
        ' 
        Label13.AutoSize = True
        Label13.Location = New Point(153, 159)
        Label13.Name = "Label13"
        Label13.Size = New Size(112, 15)
        Label13.TabIndex = 21
        Label13.Text = "Discord Web Hook: "
        ' 
        ' DiscordWebHook
        ' 
        DiscordWebHook.Location = New Point(274, 157)
        DiscordWebHook.Margin = New Padding(3, 2, 3, 2)
        DiscordWebHook.Name = "DiscordWebHook"
        DiscordWebHook.PasswordChar = "*"c
        DiscordWebHook.PlaceholderText = "<--- Discord WebHook URL --->"
        DiscordWebHook.Size = New Size(347, 23)
        DiscordWebHook.TabIndex = 22
        ' 
        ' GroupBox5
        ' 
        GroupBox5.Controls.Add(SubWindow)
        GroupBox5.Controls.Add(WebLinkT2)
        GroupBox5.Controls.Add(WebLinkT1)
        GroupBox5.Controls.Add(WebLinkOG)
        GroupBox5.Controls.Add(Label15)
        GroupBox5.Location = New Point(10, 245)
        GroupBox5.Margin = New Padding(3, 2, 3, 2)
        GroupBox5.Name = "GroupBox5"
        GroupBox5.Padding = New Padding(3, 2, 3, 2)
        GroupBox5.Size = New Size(137, 163)
        GroupBox5.TabIndex = 25
        GroupBox5.TabStop = False
        GroupBox5.Text = "Browser Source"
        ' 
        ' WebLinkT2
        ' 
        WebLinkT2.Location = New Point(5, 85)
        WebLinkT2.Margin = New Padding(3, 2, 3, 2)
        WebLinkT2.Name = "WebLinkT2"
        WebLinkT2.Size = New Size(127, 22)
        WebLinkT2.TabIndex = 1
        WebLinkT2.Text = "Translation 2"
        WebLinkT2.UseVisualStyleBackColor = True
        ' 
        ' WebLinkT1
        ' 
        WebLinkT1.Location = New Point(5, 58)
        WebLinkT1.Margin = New Padding(3, 2, 3, 2)
        WebLinkT1.Name = "WebLinkT1"
        WebLinkT1.Size = New Size(127, 22)
        WebLinkT1.TabIndex = 1
        WebLinkT1.Text = "Translation"
        WebLinkT1.UseVisualStyleBackColor = True
        ' 
        ' WebLinkOG
        ' 
        WebLinkOG.Location = New Point(5, 34)
        WebLinkOG.Margin = New Padding(3, 2, 3, 2)
        WebLinkOG.Name = "WebLinkOG"
        WebLinkOG.Size = New Size(127, 22)
        WebLinkOG.TabIndex = 1
        WebLinkOG.Text = "Original Text"
        WebLinkOG.UseVisualStyleBackColor = True
        ' 
        ' Label15
        ' 
        Label15.AutoSize = True
        Label15.Location = New Point(5, 17)
        Label15.Name = "Label15"
        Label15.Size = New Size(78, 15)
        Label15.TabIndex = 0
        Label15.Text = "Click to Copy"
        ' 
        ' CookiesName
        ' 
        CookiesName.AutoCompleteMode = AutoCompleteMode.SuggestAppend
        CookiesName.AutoCompleteSource = AutoCompleteSource.ListItems
        CookiesName.DropDownStyle = ComboBoxStyle.DropDownList
        CookiesName.FormattingEnabled = True
        CookiesName.Location = New Point(507, 40)
        CookiesName.Margin = New Padding(3, 2, 3, 2)
        CookiesName.Name = "CookiesName"
        CookiesName.Size = New Size(86, 23)
        CookiesName.TabIndex = 26
        ' 
        ' CookiesRefresh
        ' 
        CookiesRefresh.FlatStyle = FlatStyle.Flat
        CookiesRefresh.Font = New Font("Segoe UI", 8F)
        CookiesRefresh.ImageAlign = ContentAlignment.TopLeft
        CookiesRefresh.Location = New Point(598, 40)
        CookiesRefresh.Margin = New Padding(3, 2, 3, 2)
        CookiesRefresh.Name = "CookiesRefresh"
        CookiesRefresh.Size = New Size(22, 21)
        CookiesRefresh.TabIndex = 27
        CookiesRefresh.Text = "🔃"
        CookiesRefresh.UseVisualStyleBackColor = True
        ' 
        ' CheckBoxCMDBLock
        ' 
        CheckBoxCMDBLock.AutoSize = True
        CheckBoxCMDBLock.Location = New Point(153, 328)
        CheckBoxCMDBLock.Margin = New Padding(3, 2, 3, 2)
        CheckBoxCMDBLock.Name = "CheckBoxCMDBLock"
        CheckBoxCMDBLock.Size = New Size(419, 19)
        CheckBoxCMDBLock.TabIndex = 28
        CheckBoxCMDBLock.Text = "Unhide command block | If you have a weebhook set, best to keep hidden."
        CheckBoxCMDBLock.UseVisualStyleBackColor = True
        ' 
        ' SubWindow
        ' 
        SubWindow.Location = New Point(6, 110)
        SubWindow.Name = "SubWindow"
        SubWindow.Size = New Size(126, 48)
        SubWindow.TabIndex = 29
        SubWindow.Text = "Show Sub Title Window"
        SubWindow.UseVisualStyleBackColor = True
        ' 
        ' MainUI
        ' 
        AutoScaleDimensions = New SizeF(7F, 15F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(624, 674)
        Controls.Add(CheckBoxCMDBLock)
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
        Margin = New Padding(3, 2, 3, 2)
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
    Friend WithEvents PhraseTimeOutlbl As Label
    Friend WithEvents EnThreshValue As NumericUpDown
    Friend WithEvents RecordTimeoutLbl As Label
    Friend WithEvents MicCaliLbl As Label
    Friend WithEvents Label13 As Label
    Friend WithEvents DiscordWebHook As TextBox
    Friend WithEvents SetMicLbl As Label
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
    Friend WithEvents CheckBoxCMDBLock As CheckBox
    Friend WithEvents SubWindow As Button

End Class
