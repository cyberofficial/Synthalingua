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
        translatedheaderlbl = New Label()
        transcribedheaderlbl = New Label()
        MenuStrip1 = New MenuStrip()
        FontSettingsToolStripMenuItem = New ToolStripMenuItem()
        FontFaceToolStripMenuItem = New ToolStripMenuItem()
        TextColorToolStripMenuItem = New ToolStripMenuItem()
        FrontToolStripMenuItem = New ToolStripMenuItem()
        BackToolStripMenuItem = New ToolStripMenuItem()
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
        PlantToolStripMenuItem = New ToolStripMenuItem()
        FontDialog1 = New FontDialog()
        FormatToolStripMenuItem = New ToolStripMenuItem()
        BottomTextToolStripMenuItem = New ToolStripMenuItem()
        TopTextToolStripMenuItem = New ToolStripMenuItem()
        MenuStrip1.SuspendLayout()
        SuspendLayout()
        ' 
        ' InfoSaverTimer
        ' 
        ' 
        ' headertextlbl
        ' 
        headertextlbl.AutoEllipsis = True
        headertextlbl.AutoSize = True
        headertextlbl.Dock = DockStyle.Bottom
        headertextlbl.Location = New Point(0, 106)
        headertextlbl.Name = "headertextlbl"
        headertextlbl.Size = New Size(74, 15)
        headertextlbl.TabIndex = 0
        headertextlbl.Text = "Dummy Text"
        headertextlbl.Visible = False
        ' 
        ' translatedheaderlbl
        ' 
        translatedheaderlbl.AutoEllipsis = True
        translatedheaderlbl.AutoSize = True
        translatedheaderlbl.Dock = DockStyle.Bottom
        translatedheaderlbl.Location = New Point(0, 121)
        translatedheaderlbl.Name = "translatedheaderlbl"
        translatedheaderlbl.Size = New Size(74, 15)
        translatedheaderlbl.TabIndex = 1
        translatedheaderlbl.Text = "Dummy Text"
        translatedheaderlbl.Visible = False
        ' 
        ' transcribedheaderlbl
        ' 
        transcribedheaderlbl.AutoEllipsis = True
        transcribedheaderlbl.AutoSize = True
        transcribedheaderlbl.Dock = DockStyle.Bottom
        transcribedheaderlbl.Location = New Point(0, 136)
        transcribedheaderlbl.Name = "transcribedheaderlbl"
        transcribedheaderlbl.Size = New Size(74, 15)
        transcribedheaderlbl.TabIndex = 2
        transcribedheaderlbl.Text = "Dummy Text"
        transcribedheaderlbl.Visible = False
        ' 
        ' MenuStrip1
        ' 
        MenuStrip1.Dock = DockStyle.Bottom
        MenuStrip1.Items.AddRange(New ToolStripItem() {FontSettingsToolStripMenuItem, AddRemoveSubtitleControlToolStripMenuItem, PlantToolStripMenuItem, FormatToolStripMenuItem})
        MenuStrip1.Location = New Point(0, 151)
        MenuStrip1.Name = "MenuStrip1"
        MenuStrip1.Size = New Size(475, 24)
        MenuStrip1.TabIndex = 3
        MenuStrip1.Text = "MenuStrip1"
        ' 
        ' FontSettingsToolStripMenuItem
        ' 
        FontSettingsToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {FontFaceToolStripMenuItem, TextColorToolStripMenuItem})
        FontSettingsToolStripMenuItem.Name = "FontSettingsToolStripMenuItem"
        FontSettingsToolStripMenuItem.Size = New Size(88, 20)
        FontSettingsToolStripMenuItem.Text = "Font Settings"
        ' 
        ' FontFaceToolStripMenuItem
        ' 
        FontFaceToolStripMenuItem.Name = "FontFaceToolStripMenuItem"
        FontFaceToolStripMenuItem.Size = New Size(127, 22)
        FontFaceToolStripMenuItem.Text = "Font Face"
        ' 
        ' TextColorToolStripMenuItem
        ' 
        TextColorToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {FrontToolStripMenuItem, BackToolStripMenuItem})
        TextColorToolStripMenuItem.Name = "TextColorToolStripMenuItem"
        TextColorToolStripMenuItem.Size = New Size(127, 22)
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
        ' PlantToolStripMenuItem
        ' 
        PlantToolStripMenuItem.Name = "PlantToolStripMenuItem"
        PlantToolStripMenuItem.Size = New Size(46, 20)
        PlantToolStripMenuItem.Text = "Plant"
        ' 
        ' FontDialog1
        ' 
        ' 
        ' FormatToolStripMenuItem
        ' 
        FormatToolStripMenuItem.DropDownItems.AddRange(New ToolStripItem() {TopTextToolStripMenuItem, BottomTextToolStripMenuItem})
        FormatToolStripMenuItem.Name = "FormatToolStripMenuItem"
        FormatToolStripMenuItem.Size = New Size(57, 20)
        FormatToolStripMenuItem.Text = "Format"
        ' 
        ' BottomTextToolStripMenuItem
        ' 
        BottomTextToolStripMenuItem.Name = "BottomTextToolStripMenuItem"
        BottomTextToolStripMenuItem.Size = New Size(180, 22)
        BottomTextToolStripMenuItem.Text = "Bottom Text"
        ' 
        ' TopTextToolStripMenuItem
        ' 
        TopTextToolStripMenuItem.Name = "TopTextToolStripMenuItem"
        TopTextToolStripMenuItem.Size = New Size(180, 22)
        TopTextToolStripMenuItem.Text = "Top Text"
        ' 
        ' subtitlewindow
        ' 
        AutoScaleDimensions = New SizeF(7F, 15F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(475, 175)
        Controls.Add(headertextlbl)
        Controls.Add(translatedheaderlbl)
        Controls.Add(transcribedheaderlbl)
        Controls.Add(MenuStrip1)
        MainMenuStrip = MenuStrip1
        Name = "subtitlewindow"
        StartPosition = FormStartPosition.CenterScreen
        Text = "Subtitle Window"
        MenuStrip1.ResumeLayout(False)
        MenuStrip1.PerformLayout()
        ResumeLayout(False)
        PerformLayout()
    End Sub

    Friend WithEvents InfoSaverTimer As Timer
    Friend WithEvents headertextlbl As Label
    Friend WithEvents translatedheaderlbl As Label
    Friend WithEvents transcribedheaderlbl As Label
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
End Class
