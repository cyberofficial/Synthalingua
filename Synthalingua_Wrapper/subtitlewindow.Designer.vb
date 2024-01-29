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
        MenuStrip1.SuspendLayout()
        SuspendLayout()
        ' 
        ' InfoSaverTimer
        ' 
        ' 
        ' headertextlbl
        ' 
        headertextlbl.AutoSize = True
        headertextlbl.Dock = DockStyle.Top
        headertextlbl.Location = New Point(0, 24)
        headertextlbl.Name = "headertextlbl"
        headertextlbl.Size = New Size(41, 15)
        headertextlbl.TabIndex = 0
        headertextlbl.Text = "Label1"
        ' 
        ' translatedheaderlbl
        ' 
        translatedheaderlbl.AutoSize = True
        translatedheaderlbl.Dock = DockStyle.Top
        translatedheaderlbl.Location = New Point(0, 39)
        translatedheaderlbl.Name = "translatedheaderlbl"
        translatedheaderlbl.Size = New Size(41, 15)
        translatedheaderlbl.TabIndex = 1
        translatedheaderlbl.Text = "Label2"
        ' 
        ' transcribedheaderlbl
        ' 
        transcribedheaderlbl.AutoSize = True
        transcribedheaderlbl.Dock = DockStyle.Top
        transcribedheaderlbl.Location = New Point(0, 54)
        transcribedheaderlbl.Name = "transcribedheaderlbl"
        transcribedheaderlbl.Size = New Size(41, 15)
        transcribedheaderlbl.TabIndex = 2
        transcribedheaderlbl.Text = "Label3"
        ' 
        ' MenuStrip1
        ' 
        MenuStrip1.Items.AddRange(New ToolStripItem() {FontSettingsToolStripMenuItem, AddRemoveSubtitleControlToolStripMenuItem})
        MenuStrip1.Location = New Point(0, 0)
        MenuStrip1.Name = "MenuStrip1"
        MenuStrip1.Size = New Size(475, 24)
        MenuStrip1.TabIndex = 3
        MenuStrip1.Text = "MenuStrip1"
        ' 
        ' FontSettingsToolStripMenuItem
        ' 
        FontSettingsToolStripMenuItem.Name = "FontSettingsToolStripMenuItem"
        FontSettingsToolStripMenuItem.Size = New Size(88, 20)
        FontSettingsToolStripMenuItem.Text = "Font Settings"
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
        ' subtitlewindow
        ' 
        AutoScaleDimensions = New SizeF(7F, 15F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(475, 175)
        Controls.Add(transcribedheaderlbl)
        Controls.Add(translatedheaderlbl)
        Controls.Add(headertextlbl)
        Controls.Add(MenuStrip1)
        MainMenuStrip = MenuStrip1
        Name = "subtitlewindow"
        StartPosition = FormStartPosition.CenterScreen
        Text = "subtitlewindow"
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
End Class
