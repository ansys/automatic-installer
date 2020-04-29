# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Feb 17 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.adv
import wx.dataview

###########################################################################
## Class Ansys_Beta_Downloader_UI
###########################################################################

class Ansys_Beta_Downloader_UI ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 721,643 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_notebook1.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )

		self.m_panel2 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.m_panel2.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )

		bSizer32 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer2 = wx.BoxSizer( wx.VERTICAL )

		bSizer261 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer261.SetMinSize( wx.Size( 100,50 ) )

		bSizer261.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText1221 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Configuration", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1221.Wrap( -1 )

		self.m_staticText1221.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		bSizer261.Add( self.m_staticText1221, 0, wx.ALL, 5 )


		bSizer261.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer2.Add( bSizer261, 0, wx.EXPAND, 5 )

		self.m_staticline14 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline14, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Installation Root Path", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizer4.Add( self.m_staticText1, 0, wx.ALL, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.install_path_textbox = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		self.install_path_textbox.SetToolTip( u"Root path would be appended by:\n\\AnsysEM\\AnsysEMXX.X for EDT\nor \n\\ANSYS Inc\\vXXX for WB" )

		bSizer15.Add( self.install_path_textbox, 0, wx.ALL, 5 )


		bSizer15.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.set_install_path_but = wx.Button( self.m_panel2, wx.ID_ANY, u"...", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
		bSizer15.Add( self.set_install_path_but, 0, wx.ALL, 5 )


		bSizer4.Add( bSizer15, 1, wx.EXPAND, 5 )


		bSizer2.Add( bSizer4, 2, wx.EXPAND, 5 )

		self.m_staticline1 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer431 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText131 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Username", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText131.Wrap( -1 )

		bSizer431.Add( self.m_staticText131, 0, wx.ALL, 5 )

		bSizer1521 = wx.BoxSizer( wx.HORIZONTAL )

		self.username_text = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		bSizer1521.Add( self.username_text, 0, wx.ALL, 5 )


		bSizer1521.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer431.Add( bSizer1521, 1, wx.EXPAND, 5 )


		bSizer2.Add( bSizer431, 1, wx.EXPAND, 5 )

		self.m_staticline4 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer41 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText11 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Artifactory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		bSizer41.Add( self.m_staticText11, 0, wx.ALL, 5 )


		bSizer41.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		artifactory_dropmenuChoices = []
		self.artifactory_dropmenu = wx.ComboBox( self.m_panel2, wx.ID_ANY, u"Combo!", wx.DefaultPosition, wx.Size( 250,-1 ), artifactory_dropmenuChoices, wx.CB_READONLY )
		bSizer41.Add( self.artifactory_dropmenu, 0, wx.ALL, 5 )


		bSizer2.Add( bSizer41, 1, wx.EXPAND, 5 )

		bSizer43 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText13 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Artifactory Encrypted Password", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		bSizer43.Add( self.m_staticText13, 0, wx.ALL, 5 )

		bSizer152 = wx.BoxSizer( wx.HORIZONTAL )

		self.password = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), wx.TE_PASSWORD )
		self.password.SetToolTip( u"Retrieval of Artifactory Encrypted Password Instructions:\n\n1. Log into Artifactory\n\n2. Click on your username (top right)\n\n3. Enter your password to Unlock Artifactory Encrypted Password\n\n[Note] You cannot use the same artifactory password for other artifactories. Also, your encrypted password will change anytime your SSO password changes." )

		bSizer152.Add( self.password, 0, wx.ALL, 5 )


		bSizer152.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer43.Add( bSizer152, 1, wx.EXPAND, 5 )


		bSizer2.Add( bSizer43, 2, wx.EXPAND, 5 )

		self.m_staticline3 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer45 = wx.BoxSizer( wx.VERTICAL )

		self.delete_zip_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Delete downloaded ZIP", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.delete_zip_check.SetValue(True)
		bSizer45.Add( self.delete_zip_check, 0, wx.ALL, 5 )

		bSizer151 = wx.BoxSizer( wx.HORIZONTAL )

		self.download_path_textbox = wx.TextCtrl( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		self.download_path_textbox.SetToolTip( u"Download folder" )

		bSizer151.Add( self.download_path_textbox, 0, wx.ALL, 5 )


		bSizer151.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.set_download_path_but = wx.Button( self.m_panel2, wx.ID_ANY, u"...", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
		bSizer151.Add( self.set_download_path_but, 0, wx.ALL, 5 )


		bSizer45.Add( bSizer151, 1, wx.EXPAND, 5 )


		bSizer2.Add( bSizer45, 2, wx.EXPAND, 5 )

		self.m_staticline5 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer42 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText12 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Version and Product", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		bSizer42.Add( self.m_staticText12, 0, wx.ALL, 5 )


		bSizer42.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		version_dropmenuChoices = []
		self.version_dropmenu = wx.ComboBox( self.m_panel2, wx.ID_ANY, u"Combo!", wx.DefaultPosition, wx.Size( 150,-1 ), version_dropmenuChoices, wx.CB_READONLY )
		self.version_dropmenu.SetToolTip( u"Some artifactory may have different Product + Version available. This will vary from arti to arti" )

		bSizer42.Add( self.version_dropmenu, 0, wx.ALL, 5 )


		bSizer2.Add( bSizer42, 1, wx.EXPAND, 5 )

		bSizer57 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticline13 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer57.Add( self.m_staticline13, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer27 = wx.BoxSizer( wx.VERTICAL )


		bSizer27.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		bSizer30 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer30.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.install_once_button = wx.Button( self.m_panel2, wx.ID_ANY, u"Install Once", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.install_once_button.SetToolTip( u"Will install once latest available build for selected product and version" )

		bSizer30.Add( self.install_once_button, 0, 0, 5 )


		bSizer30.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer27.Add( bSizer30, 3, wx.EXPAND, 5 )


		bSizer27.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer57.Add( bSizer27, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5 )


		bSizer2.Add( bSizer57, 1, wx.EXPAND, 5 )


		bSizer32.Add( bSizer2, 5, wx.EXPAND, 5 )


		bSizer32.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		bSizer56 = wx.BoxSizer( wx.VERTICAL )

		bSizer26 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer26.SetMinSize( wx.Size( 100,50 ) )

		bSizer26.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticText122 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Autoupdate Scheduler", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText122.Wrap( -1 )

		self.m_staticText122.SetFont( wx.Font( 14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

		bSizer26.Add( self.m_staticText122, 0, wx.ALL, 5 )


		bSizer26.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer56.Add( bSizer26, 0, wx.EXPAND, 5 )

		self.m_staticline12 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer56.Add( self.m_staticline12, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer50 = wx.BoxSizer( wx.HORIZONTAL )

		self.mo_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Mo", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.mo_check, 0, wx.ALL, 5 )

		self.tu_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Tu", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.tu_check, 0, wx.ALL, 5 )

		self.we_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"We", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.we_check, 0, wx.ALL, 5 )

		self.th_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Th", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.th_check, 0, wx.ALL, 5 )

		self.fr_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Fr", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.fr_check, 0, wx.ALL, 5 )

		self.sa_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Sa", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.sa_check, 0, wx.ALL, 5 )

		self.su_check = wx.CheckBox( self.m_panel2, wx.ID_ANY, u"Su", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer50.Add( self.su_check, 0, wx.ALL, 5 )


		bSizer56.Add( bSizer50, 0, wx.EXPAND, 5 )

		bSizer51 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText19 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Update at:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )

		bSizer51.Add( self.m_staticText19, 0, wx.ALL, 5 )

		self.time_picker = wx.adv.TimePickerCtrl( self.m_panel2, wx.ID_ANY, wx.DefaultDateTime, wx.DefaultPosition, wx.DefaultSize, wx.adv.TP_DEFAULT )
		bSizer51.Add( self.time_picker, 0, wx.ALL, 5 )


		bSizer56.Add( bSizer51, 0, wx.EXPAND, 5 )


		bSizer56.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		bSizer521 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer521.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.schedule_button = wx.Button( self.m_panel2, wx.ID_ANY, u"Schedule Autoupdate", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.schedule_button.SetToolTip( u"Will schedule autoinstallation of lastest available build for selected product and version" )

		bSizer521.Add( self.schedule_button, 1, wx.EXPAND, 5 )


		bSizer521.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer56.Add( bSizer521, 0, wx.EXPAND, 5 )


		bSizer56.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.schtasks_viewlist = wx.dataview.DataViewListCtrl( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.schtasks_viewlist.SetMinSize( wx.Size( -1,250 ) )

		bSizer56.Add( self.schtasks_viewlist, 0, wx.ALL|wx.EXPAND, 5 )


		bSizer3.Add( bSizer56, 1, wx.EXPAND, 5 )

		self.m_staticline11 = wx.StaticLine( self.m_panel2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer3.Add( self.m_staticline11, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer62 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer62.Add( ( 0, 0), 5, wx.EXPAND, 5 )

		self.save_default_button = wx.Button( self.m_panel2, wx.ID_ANY, u"Save settings as Default", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer62.Add( self.save_default_button, 4, wx.ALL, 5 )


		bSizer62.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer3.Add( bSizer62, 0, wx.ALIGN_BOTTOM|wx.BOTTOM, 5 )


		bSizer32.Add( bSizer3, 5, wx.EXPAND, 5 )


		self.m_panel2.SetSizer( bSizer32 )
		self.m_panel2.Layout()
		bSizer32.Fit( self.m_panel2 )
		self.m_notebook1.AddPage( self.m_panel2, u"Main", True )
		self.m_panel4 = wx.Panel( self.m_notebook1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.m_panel4.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_APPWORKSPACE ) )

		bSizer262 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer272 = wx.BoxSizer( wx.VERTICAL )

		self.m_checkBox9 = wx.CheckBox( self.m_panel4, wx.ID_ANY, u"Force Install the same build date", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_checkBox9.SetToolTip( u"If checked will force installation of the same build date. Nor recommended to check. For example you have installed build of 20th of May and try to download and install next day, application will identify that new build was not added to artifactory and will skip the installation" )

		bSizer272.Add( self.m_checkBox9, 0, wx.ALL, 5 )

		self.m_staticline8 = wx.StaticLine( self.m_panel4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer272.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 5 )

		bSizer271 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText18 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"WB Silent Installation Flags", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		bSizer271.Add( self.m_staticText18, 0, wx.ALL, 5 )

		self.wb_flags_text = wx.TextCtrl( self.m_panel4, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		self.wb_flags_text.SetToolTip( u"Product\tProduct Flag\nMechanical APDL\t-mechapdl\nANSYS Customization Files\t-ansyscust\nANSYS Autodyn\t-autodyn\nANSYS LS-DYNA\t-lsdyna\nANSYS CFD-Post\t-cfdpost\nANSYS CFX\t-cfx\nANSYS EnSight\t-ensight\nANSYS TurboGrid\t-turbogrid\nANSYS Fluent\t-fluent\nANSYS Polyflow\t-polyflow\nANSYS ICEM CFD\t-icemcfd\nANSYS Forte\t-forte\nANSYS Chemkin\t-chemkinpro\nANSYS Energico\t-energico\nANSYS FENSAP-ICE\t-fensapice\nANSYS Reaction Workbench\t-reactionwb\nANSYS Model Fuel Library (Encrypted)\t-mfl\n# Note Installing any of the above products will install ANSYS Workbench\nANSYS Remote Solve Manager Standalone Services\t-rsm\nParasolid Geometry Interface\t-parasolid\nACIS Geometry Interface\t-acis\nNX Geometry Interface Plugin\t-ug_plugin\nANSYS Icepak\t-icepak\nCATIA 5 Reader\t-catia5_reader" )

		bSizer271.Add( self.wb_flags_text, 3, wx.ALL, 5 )


		bSizer271.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer272.Add( bSizer271, 1, wx.EXPAND, 5 )


		bSizer262.Add( bSizer272, 1, wx.EXPAND, 5 )

		bSizer29 = wx.BoxSizer( wx.VERTICAL )

		self.m_textCtrl6 = wx.TextCtrl( self.m_panel4, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer29.Add( self.m_textCtrl6, 0, wx.ALL, 5 )


		bSizer262.Add( bSizer29, 1, wx.EXPAND, 5 )


		self.m_panel4.SetSizer( bSizer262 )
		self.m_panel4.Layout()
		bSizer262.Fit( self.m_panel4 )
		self.m_notebook1.AddPage( self.m_panel4, u"Advanced Settings", False )

		bSizer1.Add( self.m_notebook1, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()
		self.status_bar = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.set_install_path_but.Bind( wx.EVT_BUTTON, self.set_install_path )
		self.artifactory_dropmenu.Bind( wx.EVT_COMBOBOX, self.populate_password )
		self.password.Bind( wx.EVT_KILL_FOCUS, self.save_question )
		self.delete_zip_check.Bind( wx.EVT_CHECKBOX, self.delete_zip_check_click )
		self.set_download_path_but.Bind( wx.EVT_BUTTON, self.set_download_path )
		self.install_once_button.Bind( wx.EVT_BUTTON, self.install_once_click )
		self.schedule_button.Bind( wx.EVT_BUTTON, self.schedule_button_click )
		self.save_default_button.Bind( wx.EVT_BUTTON, self.save_default_click )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def set_install_path( self, event ):
		event.Skip()

	def populate_password( self, event ):
		event.Skip()

	def save_question( self, event ):
		event.Skip()

	def delete_zip_check_click( self, event ):
		event.Skip()

	def set_download_path( self, event ):
		event.Skip()

	def install_once_click( self, event ):
		event.Skip()

	def schedule_button_click( self, event ):
		event.Skip()

	def save_default_click( self, event ):
		event.Skip()


