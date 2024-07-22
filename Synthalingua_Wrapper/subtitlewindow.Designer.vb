<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class subtitlewindow
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
        components = New ComponentModel.Container()
        InfoSaverTimer = New Timer(components)
        headertextlbl = New Label()
        MenuStrip1 = New MenuStrip()
        WindowSettingmsToolStripMenuItem = New ToolStripMenuItem()
        BG_Color = New ToolStripMenuItem()
        ResetBGColor = New ToolStripMenuItem()
        SaveToolStripMenuItem2 = New ToolStripMenuItem()
        SaveToolStripMenuItem3 = New ToolStripMenuItem()
        ResetToolStripMenuItem = New ToolStripMenuItem()
        FontSettingsToolStripMenuItem = New ToolStripMenuItem()
        FontFaceToolStripMenuItem = New ToolStripMenuItem()
        TextColorToolStripMenuItem = New ToolStripMenuItem()
        FrontToolStripMenuItem = New ToolStripMenuItem()
        BackToolStripMenuItem = New ToolStripMenuItem()
        LanguageModeToolStripMenuItem = New ToolStripMenuItem()
        LeftToolStripMenuItem1 = New ToolStripMenuItem()
        RightToLeftToolStripMenuItem = New ToolStripMenuItem()
        AddRemoveSubtitleControlToolStripMenuItem = New ToolStripMenuItem()
        OriginalToolStripMenuItem = New ToolStripMenuItem()
        ShowToolStripMenuItem = New ToolStripMenuItem()
        HideToolStripMenuItem = New ToolStripMenuItem()
        MainTranslationToolStripMenuItem = New ToolStripMenuItem()
        ShowToolStripMenuItem1 = New ToolStripMenuItem()
        HideToolStripMenuItem1 = New ToolStripMenuItem()
        SecondaryTranslationToolStripMenuItem = New ToolStripMenuItem()
        ShowToolStripMenuItem2 = New ToolStripMenuItem()
        HideToolStripMenuItem2 = New ToolStripMenuItem()
        FormatToolStripMenuItem = New ToolStripMenuItem()
        TopTextToolStripMenuItem = New ToolStripMenuItem()
        BottomTextToolStripMenuItem = New ToolStripMenuItem()
        RightToolStripMenuItem = New ToolStripMenuItem()
        BottomRightToolStripMenuItem = New ToolStripMenuItem()
        PlantToolStripMenuItem = New ToolStripMenuItem()
        MakeBackgroundInvisablToolStripMenuItem = New ToolStripMenuItem()
        FontDialog1 = New FontDialog()
        ColorDialog1 = New ColorDialog()
        Panel1 = New Panel()
        Panel2 = New Panel()
        MenuStrip1.SuspendLayout()
        Panel1.SuspendLayout()
        Panel2.SuspendLayout()
        SuspendLayout()
        ' 
        ' InfoSaverTimer
        ' 
        InfoSaverTimer.Interval = 500
        ' 
        ' headertextlbl
        ' 
        headertextlbl.AutoEllipsis = True
        headertextlbl.BackColor = Color.Black
        headertextlbl.Dock = DockStyle.Fill
        headertextlbl.Font = New Font("Segoe UI", 21F)
        headertextlbl.ForeColor = Color.White
        headertextlbl.Location = New Point(0, 0)
        headertextlbl.Name = "headertextlbl"
        headertextlbl.Size = New Size(793, 265)
        headertextlbl.TabIndex = 0
        headertextlbl.Text = "Dummy Text - Original"
        ' 
        ' MenuStrip1
        ' 
        MenuStrip1.Dock = DockStyle.Bottom
        MenuStrip1.Items.AddRange(New ToolStripItem() {WindowSettingmsToolStripMenuItem, FontSettingsToolStripMenuItem, AddRemoveSubtitleControlToolStripMenuItem, FormatToolStripMenuItem, PlantToolStripMenuItem, MakeBackgroundInvisablToolStripMenuItem})
        MenuStrip1.Location = New Point(0, 305)
        MenuStrip1.Name = "MenuStrip1"
        MenuStrip1.Size = New Size(827, 24)
        MenuStrip1.TabIndex = 3
        MenuStrip1.Text = "MenuStrip1"
        ' 
        ' WindowSettingmsToolStripMenuItem
        ' 
        WindowSettingmsToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {BG_Color, SaveToolStripMenuItem2})
        WindowSettingmsToolStripMenuItem.Name = "WindowSettingmsToolStripMenuItem"
        WindowSettingmsToolStripMenuItem.Size = New Size(108, 20)
        WindowSettingmsToolStripMenuItem.Text = "Window Settings"
        ' 
        ' BG_Color
        ' 
        BG_Color.DropDownItems.AddRange(New ToolStripItem() {ResetBGColor})
        BG_Color.Name = "BG_Color"
        BG_Color.Size = New Size(170, 22)
        BG_Color.Text = "Background Color"
        ' 
        ' ResetBGColor
        ' 
        ResetBGColor.Name = "ResetBGColor"
        ResetBGColor.Size = New Size(102, 22)
        ResetBGColor.Text = "Reset"
        ' 
        ' SaveToolStripMenuItem2
        ' 
        SaveToolStripMenuItem2.DropDownItems.AddRange(New ToolStripItem() {SaveToolStripMenuItem3, ResetToolStripMenuItem})
        SaveToolStripMenuItem2.Name = "SaveToolStripMenuItem2"
        SaveToolStripMenuItem2.Size = New Size(170, 22)
        SaveToolStripMenuItem2.Text = "Save"
        ' 
        ' SaveToolStripMenuItem3
        ' 
        SaveToolStripMenuItem3.Name = "SaveToolStripMenuItem3"
        SaveToolStripMenuItem3.Size = New Size(102, 22)
        SaveToolStripMenuItem3.Text = "Save"
        ' 
        ' ResetToolStripMenuItem
        ' 
        ResetToolStripMenuItem.Name = "ResetToolStripMenuItem"
        ResetToolStripMenuItem.Size = New Size(102, 22)
        ResetToolStripMenuItem.Text = "Reset"
        ' 
        ' FontSettingsToolStripMenuItem
        ' 
        FontSettingsToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {FontFaceToolStripMenuItem, TextColorToolStripMenuItem, LanguageModeToolStripMenuItem})
        FontSettingsToolStripMenuItem.Name = "FontSettingsToolStripMenuItem"
        FontSettingsToolStripMenuItem.Size = New Size(88, 20)
        FontSettingsToolStripMenuItem.Text = "Font Settings"
        ' 
        ' FontFaceToolStripMenuItem
        ' 
        FontFaceToolStripMenuItem.Name = "FontFaceToolStripMenuItem"
        FontFaceToolStripMenuItem.Size = New Size(160, 22)
        FontFaceToolStripMenuItem.Text = "Font Face"
        ' 
        ' TextColorToolStripMenuItem
        ' 
        TextColorToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {FrontToolStripMenuItem, BackToolStripMenuItem})
        TextColorToolStripMenuItem.Name = "TextColorToolStripMenuItem"
        TextColorToolStripMenuItem.Size = New Size(160, 22)
        TextColorToolStripMenuItem.Text = "Text Color"
        ' 
        ' FrontToolStripMenuItem
        ' 
        FrontToolStripMenuItem.Name = "FrontToolStripMenuItem"
        FrontToolStripMenuItem.Size = New Size(102, 22)
        FrontToolStripMenuItem.Text = "Front"
        ' 
        ' BackToolStripMenuItem
        ' 
        BackToolStripMenuItem.Name = "BackToolStripMenuItem"
        BackToolStripMenuItem.Size = New Size(102, 22)
        BackToolStripMenuItem.Text = "Back"
        ' 
        ' LanguageModeToolStripMenuItem
        ' 
        LanguageModeToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {LeftToolStripMenuItem1, RightToLeftToolStripMenuItem})
        LanguageModeToolStripMenuItem.Name = "LanguageModeToolStripMenuItem"
        LanguageModeToolStripMenuItem.Size = New Size(160, 22)
        LanguageModeToolStripMenuItem.Text = "Language Mode"
        ' 
        ' LeftToolStripMenuItem1
        ' 
        LeftToolStripMenuItem1.Name = "LeftToolStripMenuItem1"
        LeftToolStripMenuItem1.Size = New Size(140, 22)
        LeftToolStripMenuItem1.Text = "Left"
        ' 
        ' RightToLeftToolStripMenuItem
        ' 
        RightToLeftToolStripMenuItem.Name = "RightToLeftToolStripMenuItem"
        RightToLeftToolStripMenuItem.Size = New Size(140, 22)
        RightToLeftToolStripMenuItem.Text = "Right To Left"
        ' 
        ' AddRemoveSubtitleControlToolStripMenuItem
        ' 
        AddRemoveSubtitleControlToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {OriginalToolStripMenuItem, MainTranslationToolStripMenuItem, SecondaryTranslationToolStripMenuItem})
        AddRemoveSubtitleControlToolStripMenuItem.Name = "AddRemoveSubtitleControlToolStripMenuItem"
        AddRemoveSubtitleControlToolStripMenuItem.Size = New Size(175, 20)
        AddRemoveSubtitleControlToolStripMenuItem.Text = "Add/Remove Subtitle Control"
        ' 
        ' OriginalToolStripMenuItem
        ' 
        OriginalToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {ShowToolStripMenuItem, HideToolStripMenuItem})
        OriginalToolStripMenuItem.Name = "OriginalToolStripMenuItem"
        OriginalToolStripMenuItem.Size = New Size(189, 22)
        OriginalToolStripMenuItem.Text = "Original"
        ' 
        ' ShowToolStripMenuItem
        ' 
        ShowToolStripMenuItem.Name = "ShowToolStripMenuItem"
        ShowToolStripMenuItem.Size = New Size(103, 22)
        ShowToolStripMenuItem.Text = "Show"
        ' 
        ' HideToolStripMenuItem
        ' 
        HideToolStripMenuItem.Name = "HideToolStripMenuItem"
        HideToolStripMenuItem.Size = New Size(103, 22)
        HideToolStripMenuItem.Text = "Hide"
        ' 
        ' MainTranslationToolStripMenuItem
        ' 
        MainTranslationToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {ShowToolStripMenuItem1, HideToolStripMenuItem1})
        MainTranslationToolStripMenuItem.Name = "MainTranslationToolStripMenuItem"
        MainTranslationToolStripMenuItem.Size = New Size(189, 22)
        MainTranslationToolStripMenuItem.Text = "Main Translation"
        ' 
        ' ShowToolStripMenuItem1
        ' 
        ShowToolStripMenuItem1.Name = "ShowToolStripMenuItem1"
        ShowToolStripMenuItem1.Size = New Size(103, 22)
        ShowToolStripMenuItem1.Text = "Show"
        ' 
        ' HideToolStripMenuItem1
        ' 
        HideToolStripMenuItem1.Name = "HideToolStripMenuItem1"
        HideToolStripMenuItem1.Size = New Size(103, 22)
        HideToolStripMenuItem1.Text = "Hide"
        ' 
        ' SecondaryTranslationToolStripMenuItem
        ' 
        SecondaryTranslationToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {ShowToolStripMenuItem2, HideToolStripMenuItem2})
        SecondaryTranslationToolStripMenuItem.Name = "SecondaryTranslationToolStripMenuItem"
        SecondaryTranslationToolStripMenuItem.Size = New Size(189, 22)
        SecondaryTranslationToolStripMenuItem.Text = "Secondary Translation"
        ' 
        ' ShowToolStripMenuItem2
        ' 
        ShowToolStripMenuItem2.Name = "ShowToolStripMenuItem2"
        ShowToolStripMenuItem2.Size = New Size(103, 22)
        ShowToolStripMenuItem2.Text = "Show"
        ' 
        ' HideToolStripMenuItem2
        ' 
        HideToolStripMenuItem2.Name = "HideToolStripMenuItem2"
        HideToolStripMenuItem2.Size = New Size(103, 22)
        HideToolStripMenuItem2.Text = "Hide"
        ' 
        ' FormatToolStripMenuItem
        ' 
        FormatToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {TopTextToolStripMenuItem, BottomTextToolStripMenuItem, RightToolStripMenuItem, BottomRightToolStripMenuItem})
        FormatToolStripMenuItem.Name = "FormatToolStripMenuItem"
        FormatToolStripMenuItem.Size = New Size(57, 20)
        FormatToolStripMenuItem.Text = "Format"
        ' 
        ' TopTextToolStripMenuItem
        ' 
        TopTextToolStripMenuItem.Name = "TopTextToolStripMenuItem"
        TopTextToolStripMenuItem.Size = New Size(145, 22)
        TopTextToolStripMenuItem.Text = "Top Left"
        ' 
        ' BottomTextToolStripMenuItem
        ' 
        BottomTextToolStripMenuItem.Name = "BottomTextToolStripMenuItem"
        BottomTextToolStripMenuItem.Size = New Size(145, 22)
        BottomTextToolStripMenuItem.Text = "Bottom Left"
        ' 
        ' RightToolStripMenuItem
        ' 
        RightToolStripMenuItem.Name = "RightToolStripMenuItem"
        RightToolStripMenuItem.Size = New Size(145, 22)
        RightToolStripMenuItem.Text = "Top Right"
        ' 
        ' BottomRightToolStripMenuItem
        ' 
        BottomRightToolStripMenuItem.Name = "BottomRightToolStripMenuItem"
        BottomRightToolStripMenuItem.Size = New Size(145, 22)
        BottomRightToolStripMenuItem.Text = "Bottom Right"
        ' 
        ' PlantToolStripMenuItem
        ' 
        PlantToolStripMenuItem.Name = "PlantToolStripMenuItem"
        PlantToolStripMenuItem.Size = New Size(46, 20)
        PlantToolStripMenuItem.Text = "Plant"
        ' 
        ' MakeBackgroundInvisablToolStripMenuItem
        ' 
        MakeBackgroundInvisablToolStripMenuItem.Name = "MakeBackgroundInvisablToolStripMenuItem"
        MakeBackgroundInvisablToolStripMenuItem.Size = New Size(161, 20)
        MakeBackgroundInvisablToolStripMenuItem.Text = "Make Background Invisible"
        ' 
        ' FontDialog1
        ' 
        ' 
        ' Panel1
        ' 
        Panel1.Anchor = AnchorStyles.Top Or AnchorStyles.Bottom Or AnchorStyles.Left Or AnchorStyles.Right
        Panel1.Controls.Add(Panel2)
        Panel1.Location = New Point(12, 12)
        Panel1.Name = "Panel1"
        Panel1.Padding = New Padding(5)
        Panel1.Size = New Size(803, 275)
        Panel1.TabIndex = 4
        ' 
        ' Panel2
        ' 
        Panel2.Controls.Add(headertextlbl)
        Panel2.Dock = DockStyle.Fill
        Panel2.Location = New Point(5, 5)
        Panel2.Name = "Panel2"
        Panel2.Size = New Size(793, 265)
        Panel2.TabIndex = 1
        ' 
        ' subtitlewindow
        ' 
        AutoScaleDimensions = New SizeF(7F, 15F)
        AutoScaleMode = AutoScaleMode.Font
        BackColor = Color.FromArgb(CByte(0), CByte(177), CByte(64))
        ClientSize = New Size(827, 329)
        Controls.Add(Panel1)
        Controls.Add(MenuStrip1)
        MainMenuStrip = MenuStrip1
        MinimumSize = New Size(502, 183)
        Name = "subtitlewindow"
        StartPosition = FormStartPosition.CenterScreen
        Text = "Synthalingua | Caption Window"
        MenuStrip1.ResumeLayout(False)
        MenuStrip1.PerformLayout()
        Panel1.ResumeLayout(False)
        Panel2.ResumeLayout(False)
        ResumeLayout(False)
        PerformLayout()
    End Sub

    Friend WithEvents InfoSaverTimer As Timer
    Friend WithEvents headertextlbl As Label
    Friend WithEvents MenuStrip1 As MenuStrip
    Friend WithEvents FontSettingsToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents AddRemoveSubtitleControlToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents OriginalToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents ShowToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents HideToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents MainTranslationToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents ShowToolStripMenuItem1 As ToolStripMenuItem
    Friend WithEvents HideToolStripMenuItem1 As ToolStripMenuItem
    Friend WithEvents SecondaryTranslationToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents ShowToolStripMenuItem2 As ToolStripMenuItem
    Friend WithEvents HideToolStripMenuItem2 As ToolStripMenuItem
    Friend WithEvents FontDialog1 As FontDialog
    Friend WithEvents FontFaceToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents TextColorToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents FrontToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents BackToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents PlantToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents FormatToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents TopTextToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents BottomTextToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents RightToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents LanguageModeToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents LeftToolStripMenuItem1 As ToolStripMenuItem
    Friend WithEvents RightToLeftToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents WindowSettingmsToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents BG_Color As ToolStripMenuItem
    Friend WithEvents ColorDialog1 As ColorDialog
    Friend WithEvents ResetBGColor As ToolStripMenuItem
    Friend WithEvents SaveToolStripMenuItem2 As ToolStripMenuItem
    Friend WithEvents SaveToolStripMenuItem3 As ToolStripMenuItem
    Friend WithEvents ResetToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents BottomRightToolStripMenuItem As ToolStripMenuItem
    Friend WithEvents Panel1 As Panel
    Friend WithEvents Panel2 As Panel
    Friend WithEvents MakeBackgroundInvisablToolStripMenuItem As ToolStripMenuItem
End Class
