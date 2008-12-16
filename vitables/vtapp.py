# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org
#
#       $Source$
#       $Id: vtapp.py 1082 2008-10-31 12:24:08Z vmas $
#
########################################################################


"""Here is defined the VTApp class."""

__docformat__ = 'restructuredtext'

import os
import time
import re
import sets
import sys

import tables

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils
import vitables.logger as logger
import vitables.vtsplash

from  vitables.preferences import vtconfig
from  vitables.preferences import preferences

import vitables.h5db.dbsTreeModel as dbsTreeModel
import vitables.h5db.dbsTreeView as dbsTreeView

import vitables.nodes.queriesManager as qmgr
import vitables.nodes.nodeInfo as nodeInfo

import vitables.vtWidgets.inputNodeName as inputNodeName
import vitables.vtWidgets.renameDlg as renameDlg

from vitables.nodeProperties import nodePropDlg
from vitables.docBrowser import helpBrowser

import vitables.vtTables.buffer as rbuffer
import vitables.vtTables.leafModel as leafModel
import vitables.vtTables.leafView as leafView
import vitables.vtTables.dataSheet as dataSheet

class VTApp(QtGui.QMainWindow):
    """
    The application core.

    It handles the user input and controls both views and documents.
    VTApp methods can be grouped as:

    * GUI initialization and configuration methods
    * slots that handle user input
    """

    def __init__(self, mode='', dblist='', h5files=None, keep_splash=True):
        """
        Initialize the application.

        This method starts the application: makes the GUI, configure the
        app, instantiates managers needed to control the app. and connect
        signals to slots.

        :Parameters:

        - `mode`: the opening mode for files passed in the command line
        - `h5files`: a list of files to be open at startup
        - `dblist`: a file that contains a list of files to be open at startup
        """

        QtGui.QMainWindow.__init__(self)

        self.is_startup = True  # for Open file dialogs
        self.icons_dictionary = vitables.utils.getIcons()
        # Instantiate a configurator object for the application
        self.config = vtconfig.Config()

        # Show a splash screen
        logo = QtGui.QPixmap(":/icons/vitables_logo.png")
        splash = vitables.vtsplash.VTSplash(logo)
        splash.show()
        t_i = time.time()

        #
        # Make the GUI
        #
        splash.drawMessage(self.__tr('Creating the GUI...',
            'A splash screen message'))
        self.setWindowTitle(self.__tr('ViTables %s' % vtconfig.getVersion(),
            'Main window title'))
        self.setIconSize(QtCore.QSize(22, 22))
        self.setWindowIcon(self.icons_dictionary['vitables_wm'])
        central_widget = QtGui.QWidget(self)
        central_layout = QtGui.QVBoxLayout(central_widget)
        self.vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical, central_widget)
        central_layout.addWidget(self.vsplitter)
        self.setCentralWidget(central_widget)

        # The vertical splitter divides the screen into 2 regions
        self.hsplitter = QtGui.QSplitter(self.vsplitter)
        self.logger = logger.Logger(self.vsplitter)

        # The top region of the screen is divided by a splitter
        self.dbs_tree_view = dbsTreeView.DBsTreeView(self, self.hsplitter)
        self.workspace = QtGui.QMdiArea(self.hsplitter)
        sb_as_needed = QtCore.Qt.ScrollBarAsNeeded
        self.workspace.setHorizontalScrollBarPolicy(sb_as_needed)
        self.workspace.setVerticalScrollBarPolicy(sb_as_needed)
        self.workspace.setWhatsThis(self.__tr(
            """<qt>
            <h3>The Workspace</h3>
            This is the area where open leaves of the object tree are
            displayed. Many tables and arrays can be displayed
            simultaneously.
            <p>The diferent views can be tiled as a mosaic or stacked as
            a cascade.
            </qt>""",
            'WhatsThis help for the workspace')
            )

        # The signal mapper used to keep the the Windows menu updated
        self.window_mapper = QtCore.QSignalMapper(self)
        self.connect(self.window_mapper, QtCore.SIGNAL("mapped(QWidget*)"), 
            self.workspace.setActiveSubWindow)
        # The following version of the previous connect doesn't work
        # I think it's a pyqt bug
        #self.window_mapper = QtCore.QSignalMapper(self)
        #self.connect(self.window_mapper, QtCore.SIGNAL("mapped(QWidget*)"), 
        #            self.workspace, 
        #            QtCore.SLOT("setActiveSubWindow(QMdiSubWindow*)"))

        self.gui_actions = self.setupActions()
        self.setupToolBars()
        self.setupMenus()
        self.initStatusBar()
        self.logger.nodeCopyAction = self.gui_actions['nodeCopy']

        # Redirect standard output and standard error to a Logger instance
        sys.stdout = self.logger
        sys.stderr = self.logger

        # Apply the configuration stored on disk
        splash.drawMessage(self.__tr('Configuration setup...',
            'A splash screen message'))
        self.loadConfiguration(self.readConfiguration())

        # Print the welcome message
        print self.__tr('''ViTables %s\nCopyright (c) 2008 Vicent Mas.'''
            '''\nAll rights reserved.''' % vtconfig.getVersion(),
            'Application startup message')

        # The tree of databases model/view
        self.dbs_tree_model = dbsTreeModel.DBsTreeModel(self)
        self.dbs_tree_view.setModel(self.dbs_tree_model)
        self.queries_mgr = \
                    qmgr.QueriesManager(self.dbs_tree_model.tmp_dbdoc.h5file)

        # The list of most recently open DBs
        self.number_of_recent_files = 10
        while self.recent_files.count() > self.number_of_recent_files:
            self.recent_files.takeLast()
        # The File Browser History
        self.file_selector_history = QtCore.QStringList()
        # List of HelpBrowser instances in memory
        self.doc_browsers = []

        # Restore last session
        if self.restore_last_session:
            splash.drawMessage(self.__tr('Recovering last session...',
                'A splash screen message'))
            self.recoverLastSession()

        # Process the command line
        if h5files:
            splash.drawMessage(self.__tr('Opening files...',
                'A splash screen message'))
            self.processCommandLineArgs(mode=mode, h5files=h5files)
        elif dblist:
            splash.drawMessage(self.__tr('Opening the list of files...',
                'A splash screen message'))
            self.processCommandLineArgs(dblist=dblist)

        # Make sure that the splash screen is shown at least for two seconds
        if keep_splash:
            t_f = time.time()
            while t_f - t_i < 2:
                t_f = time.time()
        splash.finish(self)
        del splash

        # Ensure that QActions have a consistent state
        self.slotUpdateActions()

        self.connect(self.dbs_tree_model, \
            QtCore.SIGNAL('rowsRemoved(QModelIndex, int, int)'), 
            self.slotUpdateActions)
        self.connect(self.dbs_tree_model, \
            QtCore.SIGNAL('rowsInserted(QModelIndex, int, int)'), 
            self.slotUpdateActions)
        self.connect(self.dbs_tree_model, QtCore.SIGNAL('nodeAdded'), \
            self.dbs_tree_view.expand)

        self.slotUpdateWindowsMenu()

        self.workspace.installEventFilter(self)


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate('VTApp', source, comment))


    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        actions = {}
        actions['fileNew'] = vitables.utils.createAction(self, 
            self.__tr('&New', 'File -> New'), QtGui.QKeySequence.New, 
            self.slotFileNew, self.icons_dictionary['filenew'], 
            self.__tr('Create a new file', 
                'Status bar text for the File -> New action'))

        actions['fileOpen'] = vitables.utils.createAction(self, 
            self.__tr('&Open...', 'File -> Open'), QtGui.QKeySequence.Open, 
            self.slotFileOpen, self.icons_dictionary['fileopen'], 
            self.__tr('Open an existing file',
                'Status bar text for the File -> Open action'))

        actions['fileOpenRO'] = vitables.utils.createAction(self, 
            self.__tr('Read-only open...', 'File -> Open'), None, 
            self.slotFileOpenRO, self.icons_dictionary['fileopen'], 
            self.__tr('Open an existing file in read-only mode',
                'Status bar text for the File -> Open action'))

        actions['fileClose'] = vitables.utils.createAction(self, 
            self.__tr('&Close', 'File -> Close'), QtGui.QKeySequence.Close, 
            self.slotFileClose, self.icons_dictionary['fileclose'], 
            self.__tr('Close the selected file',
                'Status bar text for the File -> Close action'))

        actions['fileCloseAll'] = vitables.utils.createAction(self, 
            self.__tr('Close &All', 'File -> Close All'), None, 
            self.slotFileCloseAll, None, 
            self.__tr('Close all files',
                'Status bar text for the File -> Close All action'))

        actions['fileSaveAs'] = vitables.utils.createAction(self, 
            self.__tr('&Save as...', 'File -> Save As'), 
            QtGui.QKeySequence('CTRL+SHIFT+S'), 
            self.slotFileSaveAs, self.icons_dictionary['filesaveas'], 
            self.__tr('Save a renamed copy of the selected file',
                'Status bar text for the File -> Save As action'))

        actions['fileExit'] = vitables.utils.createAction(self, 
            self.__tr('E&xit', 'File -> Exit'), QtGui.QKeySequence('CTRL+Q'), 
            self.slotFileExit, self.icons_dictionary['exit'], 
            self.__tr('Quit ViTables',
                'Status bar text for the File -> Exit action'))

        actions['nodeOpen'] = vitables.utils.createAction(self, 
            self.__tr('&Open view', 'Node -> Open View'), 
            QtGui.QKeySequence('CTRL+SHIFT+O'), 
            self.slotNodeOpen, None, 
            self.__tr('Display the contents of the selected node', 
                'Status bar text for the Node -> Open View action'))

        actions['nodeClose'] = vitables.utils.createAction(self, 
            self.__tr('C&lose view', 'Node -> Close View'), 
            QtGui.QKeySequence('CTRL+SHIFT+W'), 
            self.slotNodeClose, None, 
            self.__tr('Close the view of the selected node', 
                'Status bar text for the Node -> Close View action'))

        actions['nodeProperties'] = vitables.utils.createAction(self, 
            self.__tr('Prop&erties...', 'Node -> Properties'), 
            QtGui.QKeySequence('CTRL+I'), 
            self.slotNodeProperties, self.icons_dictionary['info'], 
            self.__tr('Show the properties dialog for the selected node', 
                'Status bar text for the Node -> Properties action'))

        actions['nodeNew'] = vitables.utils.createAction(self, 
            self.__tr('&New group...', 'Node -> New group'), 
            QtGui.QKeySequence('CTRL+SHIFT+N'), 
            self.slotNodeNewGroup, self.icons_dictionary['folder_new'], 
            self.__tr('Create a new group under the selected node', 
                'Status bar text for the Node -> New group action'))

        actions['nodeRename'] = vitables.utils.createAction(self, 
            self.__tr('&Rename...', 'Node -> Rename'), 
            QtGui.QKeySequence('CTRL+R'), 
            self.slotNodeRename, None, 
            self.__tr('Rename the selected node', 
                'Status bar text for the Node -> Rename action'))

        actions['nodeCut'] = vitables.utils.createAction(self, 
            self.__tr('Cu&t', 'Node -> Cut'), QtGui.QKeySequence('CTRL+X'), 
            self.slotNodeCut, self.icons_dictionary['editcut'], 
            self.__tr('Cut the selected node', 
                'Status bar text for the Node -> Cut action'))

        actions['nodeCopy'] = vitables.utils.createAction(self, 
            self.__tr('&Copy', 'Node -> Copy'), QtGui.QKeySequence.Copy, 
            self.slotNodeCopy, self.icons_dictionary['editcopy'], 
            self.__tr('Copy the selected node', 
                'Status bar text for the Node -> Copy action'))

        actions['nodePaste'] = vitables.utils.createAction(self, 
            self.__tr('&Paste', 'Node -> Paste'), QtGui.QKeySequence.Paste, 
            self.slotNodePaste, self.icons_dictionary['editpaste'], 
            self.__tr('Paste the last copied/cut node', 
                'Status bar text for the Node -> Copy action'))

        actions['nodeDelete'] = vitables.utils.createAction(self, 
            self.__tr('&Delete', 'Node -> Delete'), QtGui.QKeySequence.Delete, 
            self.slotNodeDelete, self.icons_dictionary['editdelete'], 
            self.__tr('Delete the selected node', 
                'Status bar text for the Node -> Copy action'))

        actions['queryNew'] = vitables.utils.createAction(self, 
            self.__tr('&New...', 'Query -> New...'), None, 
            self.slotQueryNew, self.icons_dictionary['new_filter'], 
            self.__tr('Create a new filter for the selected table', 
                'Status bar text for the Query -> New... action'))

        actions['queryDeleteAll'] = vitables.utils.createAction(self, 
            self.__tr('Delete &All', 'Query -> Delete All'), None, 
            self.slotQueryDeleteAll, 
            self.icons_dictionary['delete_filters'], 
            self.__tr('Remove all filters', 
                'Status bar text for the Query -> Delete All action'))

        actions['windowCascade'] = vitables.utils.createAction(self, 
            self.__tr('&Cascade', 'Windows -> Cascade'), None, 
            self.workspace.cascadeSubWindows, None, 
            self.__tr('Arranges open windows in a cascade pattern', 
                'Status bar text for the Windows -> Cascade action'))

        actions['windowTile'] = vitables.utils.createAction(self, 
            self.__tr('&Tile', 'Windows -> Tile'), None, 
            self.workspace.tileSubWindows, None, 
            self.__tr('Arranges open windows in a tile pattern', 
                'Status bar text for the Windows -> Tile action'))

        actions['windowRestoreAll'] = vitables.utils.createAction(self, 
            self.__tr('&Restore All', 'Windows -> Restore All'), None, 
            self.slotWindowsRestoreAll, None, 
            self.__tr('Restore all minimized windows on the workspace', 
                'Status bar text for the Windows -> Restore All action'))

        actions['windowMinimizeAll'] = vitables.utils.createAction(self, 
            self.__tr('&Minimize All', 'Windows -> Minimize All'), None, 
            self.slotWindowsMinimizeAll, None, 
            self.__tr('Minimize all windows on the workspace', 
                'Status bar text for the Windows -> Restore All action'))

        actions['windowClose'] = vitables.utils.createAction(self, 
            self.__tr('C&lose', 'Windows -> Close'), None, 
            self.slotWindowsClose, None, 
            self.__tr('Close the active view', 
                'Status bar text for the Windows -> Close action'))

        actions['windowCloseAll'] = vitables.utils.createAction(self, 
            self.__tr('Close &All', 'Windows -> Close All'), None, 
            self.slotWindowsCloseAll, None, 
            self.__tr('Close all views', 
                'Status bar text for the Windows -> Close All action'))

        actions['windowsActionGroup'] = QtGui.QActionGroup(self)

        actions['mdiTabbed'] = vitables.utils.createAction(self, 
            self.__tr('Change view mode', 'MDI -> Tabbed'), None, 
            self.changeMDIViewMode, 
            None, 
            self.__tr('Change the workspace view mode', 
                'Status bar text for the MDI -> Tabbed action'))

        actions['toolsUserOptions'] = vitables.utils.createAction(self, 
            self.__tr('&Preferences...', 'Tools -> Preferences'), None, 
            self.slotToolsPreferences, 
            self.icons_dictionary['appearance'], 
            self.__tr('Configure ViTables', 
                'Status bar text for the Tools -> Preferences action'))

        actions['helpUsersGuide'] = vitables.utils.createAction(self, 
            self.__tr("&User's Guide", 'Help -> Users Guide'), 
            QtGui.QKeySequence.HelpContents, 
            self.slotHelpDocBrowser, 
            self.icons_dictionary['usersguide'], 
            self.__tr('Open a HelpBrowser window',
                    'Status bar text for the Help -> Users Guide action'))

        actions['helpAbout'] = vitables.utils.createAction(self, 
            self.__tr('&About', 'Help -> About'), None, 
            self.slotHelpAbout, None, 
            self.__tr('Display information about ViTables',
                    'Status bar text for the Help -> About action'))

        actions['helpAboutQt'] = vitables.utils.createAction(self, 
            self.__tr('About &Qt', 'Help -> About Qt'), None, 
            self.slotHelpAboutQt, None, 
            self.__tr('Display information about the Qt library',
                    'Status bar text for the Help -> About Qt action'))

        actions['helpVersions'] = vitables.utils.createAction(self, 
            self.__tr('Show &Versions', 'Help -> Show Versions'), None, 
            self.slotHelpVersions, None, 
            self.__tr('Show the versions of the libraries used by ViTables',
                    'Status bar text for the Help -> Show Versions action'))

        return actions


    def setupToolBars(self):
        """
        Set up the main window toolbars.

        Toolbars are made of actions.
        """

        # File toolbar
        self.file_toolbar = self.addToolBar(self.__tr('File operations', 
            'Toolbar title'))
        # Warning! Do NOT use 'File toolbar' as a object name or it will
        # show an strange behaviour (a Qt bug I think): it will always
        # be added to the left and will expand the whole top area
        self.file_toolbar.setObjectName('File')
        actions = ['fileNew', 'fileOpen', 'fileClose', 'fileSaveAs', 
                   'fileExit']
        vitables.utils.addActions(self.file_toolbar, actions, self.gui_actions)

        # Reset the tooltip of the File -> Open... button
        file_open_button = self.file_toolbar.widgetForAction(
            self.gui_actions['fileOpen'])
        file_open_button.setToolTip(self.__tr("""Click to open a """
            """file\nClick and hold to open a recent file""",
            'File toolbar -> Open Recent Files'))

        # Node toolbar
        self.node_toolbar = self.addToolBar(self.__tr('Node operations', 
            'Toolbar title'))
        self.node_toolbar.setObjectName('Node toolbar')
        actions = ['nodeNew', 'nodeCut', 'nodeCopy', 'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.node_toolbar, actions, self.gui_actions)

        # Query toolbar
        self.query_toolbar = self.addToolBar(self.__tr('Queries on tables', 
            'Toolbar title'))
        self.query_toolbar.setObjectName('Query toolbar')
        actions = ['queryNew', 'queryDeleteAll']
        vitables.utils.addActions(self.query_toolbar, actions, 
                                    self.gui_actions)

        # Help toolbar
        self.help_toolbar = self.addToolBar(self.__tr('Help system', 
            'Toolbar title'))
        self.help_toolbar.setObjectName('Help toolbar')
        actions = ['helpUsersGuide']
        vitables.utils.addActions(self.help_toolbar, actions, self.gui_actions)
        whatis = QtGui.QWhatsThis.createAction(self.help_toolbar)
        whatis.setStatusTip(self.__tr('Context help',
                    'Status bar text for the Help -> Whats This action'))
        self.help_toolbar.addAction(whatis)


    def setupMenus(self):
        """
        Set up the main window menus.

        Popus are made of actions, items and separators.
        The Windows menu is a special case due to its dynamic nature.
        The menu contents depend on the number of existing views.
        In order to track changes and keep updated the menu, it is reloaded
        every time it is about to be displayed. This goal is achieved using
        signal/slot mechanism (see code below).
        """

        # Create the File menu and add actions/submenus/separators to it
        file_menu = self.menuBar().addMenu(self.__tr("&File", 
            'The File menu entry'))
        self.open_recent_submenu = QtGui.QMenu(self.__tr('Open R&ecent Files',
            'File -> Open Recent Files'))
        self.open_recent_submenu.setSeparatorsCollapsible(False)
        file_actions = ['fileNew', 'fileOpen', 'fileOpenRO', 
            self.open_recent_submenu, None, 'fileClose', 'fileCloseAll', None, 
            'fileSaveAs', None, 'fileExit']
        vitables.utils.addActions(file_menu, file_actions, self.gui_actions)

        file_open_button = self.file_toolbar.widgetForAction(
            self.gui_actions['fileOpen'])
        file_open_button.setMenu(self.open_recent_submenu)
        self.connect(self.open_recent_submenu, QtCore.SIGNAL("aboutToShow()"), 
            self.slotUpdateRecentSubmenu)

        # Create the Node menu and add actions/submenus/separators to it
        node_menu = self.menuBar().addMenu(self.__tr("&Node", 
            'The Node menu entry'))
        node_actions = ['nodeOpen', 'nodeClose', 'nodeProperties', None, 
            'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy', 'nodePaste', 
            'nodeDelete']
        vitables.utils.addActions(node_menu, node_actions, self.gui_actions)

        # Create the Query menu and add actions/submenus/separators to it
        query_menu = self.menuBar().addMenu(self.__tr("&Query", 
            'The Query menu entry'))
        query_actions = ['queryNew', None, 'queryDeleteAll']
        vitables.utils.addActions(query_menu, query_actions, self.gui_actions)

        # Create the Windows menu and add actions/menus/separators to it
        self.windows_menu = self.menuBar().addMenu(self.__tr("&Windows", 
            'The Windows menu entry'))
        self.windows_menu
        action_group = QtGui.QActionGroup(self.windows_menu)
        action_group.setExclusive(True)
        self.windows_menu.action_group = action_group
        self.connect(self.windows_menu, QtCore.SIGNAL("aboutToShow()"), 
            self.slotUpdateWindowsMenu)

        # Create the Help menu and add actions/menus/separators to it
        help_menu = self.menuBar().addMenu(self.__tr("&Help", 
            'The Help menu entry'))
        help_actions = ['helpUsersGuide', None, 'helpAbout', 'helpAboutQt', 
            'helpVersions', None]
        vitables.utils.addActions(help_menu, help_actions, self.gui_actions)
        whatis = QtGui.QWhatsThis.createAction(help_menu)
        whatis.setStatusTip(self.__tr('Context help',
                    'Status bar text for the Help -> Whats This action'))
        help_menu.addAction(whatis)

        # Create the Tools menu and add actions/submenus/separators to it
        tools_menu = QtGui.QMenu(self.__tr("&Tools", 'The Tools menu entry'),
                                 self.menuBar())
        self.menuBar().insertMenu(self.menuBar().actions()[-1], tools_menu)

        # The popup containing checkable entries for the toolbars and
        # dock widgets present in the main window
        self.hide_toolbar_submenu = self.createPopupMenu()
        self.hide_toolbar_submenu.menuAction().setText(self.__tr('ToolBars', 
                                                'Tools -> ToolBars action'))
        tools_actions = ['toolsUserOptions', None, self.hide_toolbar_submenu]
        vitables.utils.addActions(tools_menu, tools_actions, self.gui_actions)

        #########################################################
        #
        # 					Context menus
        #
        #########################################################

        self.view_cm = QtGui.QMenu()
        actions = ['fileNew', 'fileOpen', 'fileOpenRO', 
            self.open_recent_submenu, None, 'fileClose', 'fileCloseAll', None, 
            'fileSaveAs', None, 'fileExit']
        vitables.utils.addActions(self.view_cm, actions, self.gui_actions)

        self.root_node_cm = QtGui.QMenu()
        actions = ['fileClose', 'fileSaveAs', None, 'nodeProperties', None, 
            'nodeNew', 'nodeCopy', 'nodePaste', None, 'queryDeleteAll']
        vitables.utils.addActions(self.root_node_cm, actions, self.gui_actions)

        self.group_node_cm = QtGui.QMenu()
        actions = ['nodeProperties', None, 'nodeNew', 'nodeRename', 'nodeCut', 
            'nodeCopy', 'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.group_node_cm, actions, 
                                    self.gui_actions)

        self.leaf_node_cm = QtGui.QMenu()
        actions = ['nodeOpen', 'nodeClose', None, 'nodeProperties', None, 
            'nodeRename', 'nodeCut', 'nodeCopy', 'nodePaste', 'nodeDelete', 
            None, 'queryNew']
        vitables.utils.addActions(self.leaf_node_cm, actions, self.gui_actions)

        self.mdi_cm = QtGui.QMenu()
        actions = ['mdiTabbed', None, 
            self.windows_menu]
        vitables.utils.addActions(self.mdi_cm, actions, self.gui_actions)

    def initStatusBar(self):
        """Init status bar."""

        status_bar = self.statusBar()
        self.sb_node_info = QtGui.QLabel(status_bar)
        self.sb_node_info.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, \
                                        QtGui.QSizePolicy.Minimum)
        status_bar.addPermanentWidget(self.sb_node_info)
        self.sb_node_info.setToolTip(self.__tr(
            'The node currently selected in the Tree of databases pane',
            'The Selected node box startup message'))
        status_bar.showMessage(self.__tr('Ready...',
            'The status bar startup message'))


    def readConfiguration(self):
        """
        Get the application configuration currently stored on disk.

        Read the configuration from the stored settings. If a setting
        cannot be read (as it happens when the package is just
        installed) then its default value is returned.
        Geometry and Recent settings are returned as lists, color
        settings as QColor instances. The rest of settings are returned
        as QStrings or integers.

        :Returns: a dictionary with the configuration stored on disk
        """

        config = {}
        config['Logger/Paper'] = self.config.loggerPaper()
        config['Logger/Text'] = self.config.loggerText()
        config['Logger/Font'] = self.config.loggerFont()
        config['Workspace/Background'] = self.config.workspaceBackground()
        config['Startup/restoreLastSession'] = self.config.startupLastSession()
        config['Startup/startupWorkingDir'] = self.config.startupWorkingDir()
        config['Startup/lastWorkingDir'] = self.config.lastWorkingDir()
        config['Geometry/Position'] = self.config.windowPosition()
        config['Geometry/Layout'] = self.config.windowLayout()
        config['Geometry/HSplitter'] = self.config.hsplitterPosition()
        config['Geometry/VSplitter'] = self.config.vsplitterPosition()
        config['Recent/Files'] = self.config.recentFiles()
        config['Session/Files'] = self.config.sessionFiles()
        config['HelpBrowser/History'] = self.config.helpHistory()
        config['HelpBrowser/Bookmarks'] = self.config.helpBookmarks()
        config['Look/currentStyle'] = self.config.readStyle()
        return config


    def loadConfiguration(self, config):
        """
        Configure the application with the given configuration/preferences.

        :Parameter config: a dictionary with the configuration/preferences
                           being loaded
        """

        keys = config.keys()
        for key in keys:
            value = config[key]
            if key == 'Logger/Paper':
                paper = str(QtGui.QColor(value).name())
                stylesheet = self.logger.styleSheet()
                old_paper = stylesheet[-7:]
                stylesheet.replace(old_paper, paper)
                self.logger.setStyleSheet(stylesheet)
            elif key == 'Logger/Text':
                text_color = QtGui.QColor(value)
                self.logger.moveCursor(QtGui.QTextCursor.End)
                self.logger.setTextColor(text_color)
            elif key == 'Logger/Font':
                self.logger.setFont(QtGui.QFont(value))
            elif key == 'Workspace/Background':
                self.workspace.setBackground(QtGui.QBrush(value))
            elif key == 'Look/currentStyle':
                # Default style is provided by the underlying window manager
                self.current_style = value.toString()
                if self.current_style != 'default':
                    QtGui.qApp.setStyle(self.current_style)
            elif key == 'Geometry/Position':
                # Default position is provided by the underlying window manager
                if value.isValid():
                    self.restoreGeometry(value.toByteArray())
            elif key == 'Geometry/Layout':
                # Default layout is provided by the underlying Qt installation
                if value.isValid():
                    self.restoreState(value.toByteArray())
            elif key == 'Geometry/HSplitter':
                # Default geometry provided by the underlying Qt installation
                if value.isValid():
                    self.hsplitter.restoreState(value.toByteArray())
            elif key == 'Geometry/VSplitter':
                # Default geometry provided by the underlying Qt installation
                if value.isValid():
                    self.vsplitter.restoreState(value.toByteArray())
            elif key == 'Startup/restoreLastSession':
                self.restore_last_session = value.toBool()
            elif key == 'Startup/startupWorkingDir':
                self.startup_working_directory = value.toString()
            elif key == 'Startup/lastWorkingDir':
                self.last_working_directory = value.toString()
            elif key == 'Recent/Files':
                self.recent_files = value.toStringList()
            elif key == 'Session/Files':
                self.session_files_nodes = value.toStringList()
            elif key == 'HelpBrowser/History':
                self.hb_history = value.toStringList()
            elif key == 'HelpBrowser/Bookmarks':
                self.hb_bookmarks = value.toStringList()


    def saveConfiguration(self):
        """
        Store current application settings on disk.

        Note that we are using ``QSettings`` for writing to the config file,
        so we **must** rely on its searching algorithms in order to find
        that file.
        """

        # Logger paper
        style_sheet = self.logger.styleSheet()
        paper = style_sheet[-7:]
        self.config.writeValue('Logger/Paper', QtGui.QColor(paper))
        # Logger text color
        self.config.writeValue('Logger/Text', self.logger.textColor())
        # Logger text font
        self.config.writeValue('Logger/Font', self.logger.font())
        # Workspace
        self.config.writeValue('Workspace/Background', 
            self.workspace.background())
        # Style
        self.config.writeValue('Look/currentStyle', self.current_style)
        # Startup working directory
        self.config.writeValue('Startup/startupWorkingDir', 
            self.startup_working_directory)
        # Startup restore last session
        self.config.writeValue('Startup/restoreLastSession', 
            self.restore_last_session)
        # Startup last working directory
        self.config.writeValue('Startup/lastWorkingDir', 
            self.last_working_directory)
        # Window geometry
        self.config.writeValue('Geometry/Position', self.saveGeometry())
        # Window layout
        self.config.writeValue('Geometry/Layout', self.saveState())
        # Horizontal splitter geometry
        self.config.writeValue('Geometry/HSplitter', 
                            self.hsplitter.saveState())
        # Vertical splitter geometry
        self.config.writeValue('Geometry/VSplitter', 
                            self.vsplitter.saveState())
        # The list of recent files
        self.config.writeValue('Recent/Files', self.recent_files)
        # The list of session files and nodes
        self.session_files_nodes = self.getSessionFilesNodes()
        self.config.writeValue('Session/Files', self.session_files_nodes)
        # The Help Browser history
        self.config.writeValue('HelpBrowser/History', self.hb_history)
        # The Help Browser bookmarks
        self.config.writeValue('HelpBrowser/Bookmarks', self.hb_bookmarks)
        # If we don't sync then errors appear for every QColor and QFont
        # instances trying to be saved
        # QVariant::load: unable to load type 67 (appears 3 times)
        # QVariant::load: unable to load type 64 (appears 1 time)
        self.config.sync()


    def getSessionFilesNodes(self):
        """
        The list of files and nodes currently open.

        The current session state is grabbed from the tracking
        dictionaries managed by the leaves manager and the db manager.
        The list looks like::

            ['mode#@#filepath1#@#nodepath1#@#nodepath2, ...',
            'mode#@#filepath2#@#nodepath1#@#nodepath2, ...', ...]
        """

        session_files_nodes = QtCore.QStringList([])
        # The list of files returned by getDBList doesn't include the temporary
        # database
        filepaths = self.dbs_tree_model.getDBList()
        node_views = [window for window in self.workspace.subWindowList() \
                        if isinstance(window, dataSheet.DataSheet)]
        for path in filepaths:
            mode = self.dbs_tree_model.getDBDoc(path).mode
            # If a new file has been created during the current session
            # then write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            if mode == 'w':
                mode = 'a'
            item_path = '%s#@#%s' % (mode, path)
            for view in node_views:
                if view.leaf.filepath == path:
                    item_path = '%s#@#%s' % (item_path, view.leaf.nodepath)
            session_files_nodes.append(item_path)

        # Format the list in a handy way to store it on disk
        return session_files_nodes


    # Databases are automatically opened at startup when:
    # 
    #     * application is configured for recovering last session
    #     * ViTables is started from the command line with some args
    #

    def recoverLastSession(self):
        """
        Recover the last session.

        This method will attempt to open those files and leaf views that
        were opened the last time the user closed ViTables.
        The lists of files and leaves is read from the configuration.
        The format is::

            ['mode#@#filepath1#@#nodepath1#@#nodepath2, ...',
            'mode#@#filepath2#@#nodepath1#@#nodepath2, ...', ...]
        """

        expanded_signal = QtCore.SIGNAL("expanded(QModelIndex)")
        for file_data in self.session_files_nodes:
            item = str(file_data).split('#@#')
            # item looks like [mode, filepath1, nodepath1, nodepath2, ...]
            mode = item.pop(0)
            filepath = item.pop(0)
            filepath = vitables.utils.forwardPath(filepath)
            # Open the database --> add the root group to the tree view.
            self.dbs_tree_model.openDBDoc(filepath, mode)
            db_doc = self.dbs_tree_model.getDBDoc(filepath)
            if db_doc is None:
                continue
            # Update the history file
            self.updateRecentFiles(filepath, mode)

            # For opening a node the groups in the nodepath are expanded
            # left to right letting the lazy population feature to work
            for nodepath in item:  # '/group1/group2/...groupN/leaf'
                # Check if the node still exists because the database
                # could have changed since last ViTables session
                node = db_doc.getNode(nodepath)
                if node is None:
                    continue
                # groups is ['', 'group1', 'group2', ..., 'groupN']
                groups = nodepath.split('/')[:-1]
                # Expands the top level group, i.e., the root group.
                # It happens to be the last root node added to model
                # so its row is 0
                group = self.dbs_tree_model.root.childAtRow(0)
                index = self.dbs_tree_model.index(0, 0, QtCore.QModelIndex())
                self.dbs_tree_view.emit(expanded_signal, index)
                groups.pop(0)
                # Expand the rest of groups of the nodepath
                while groups != []:
                    parent_group = group
                    parent_index = index
                    group = parent_group.findChild(groups[0])
                    row = group.row()
                    index = self.dbs_tree_model.index(row, 0, parent_index)
                    self.dbs_tree_view.emit(expanded_signal, index)
                    groups.pop(0)
                # Finally we open the leaf
                leaf_name = nodepath.split('/')[-1]
                leaf = group.findChild(leaf_name)
                row = leaf.row()
                self.slotNodeOpen(self.dbs_tree_model.index(row, 0, index))


    def processCommandLineArgs(self, mode='', h5files=None, dblist=''):
        """Open files passed in the command line."""

        bad_line = self.__tr("""Opening failed: wrong mode or path in %s""", 
                            'Bad line format')
        # The database manager opens the files (if any)
        if isinstance(h5files, list):
            for filepath in h5files:
                filepath = vitables.utils.forwardPath(filepath)
                self.dbs_tree_model.openDBDoc(filepath, mode)
                self.updateRecentFiles(filepath, mode)

        # If a list of files is passed then parse the list and open the files
        if dblist:
            try:
                input_file = open(dblist, 'r')
                lines = [l[:-1].split('#@#') for l in input_file.readlines()]
                input_file.close()
                for line in lines:
                    if len(line) !=2:
                        print bad_line % line
                        continue
                    mode, filepath = line
                    filepath = vitables.utils.forwardPath(filepath)
                    if not mode in ['r', 'a']:
                        print bad_line % line
                        continue
                    self.dbs_tree_model.openDBDoc(filepath, mode)
                    self.updateRecentFiles(filepath, mode)
            except IOError:
                print self.__tr("""\nError: list of HDF5 files not read""",
                                'File not updated error')


    def closeEvent(self, event):
        """
        Handle close events.

        Clicking the close button of the main window titlebar causes
        the application quitting immediately, leaving things in a non
        consistent state. This event handler ensures that the needed
        tidy up is done before to quit.
        """

        # Main window close button clicked
        self.slotFileExit()


    # Updating appearance means:
    # 
    #     * changing the toolbar buttons look when their tied QActions are
    #       enabled/disabled
    #     * updating content of menus and submenus
    # 
    # Updating state means:
    # 
    #     * toggling state of QActions i.e. enabling/disabling QActions
    # 

    def slotUpdateActions(self):
        """
        Update the state of the actions tied to menu items and toolbars.

        Every time that the selected item changes in the tree viewer the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.).
        The following events trigger a call to this method:

            * insertion/deletion of rows in the tree of databases model
              (see VTApp.slotUpdateCurrent method)
            * changes in the selection state of the tree of databases view
              (see DBsTreeView.currentChanged method)

        The slot should be manually called when a new view is activated in
        the workspace (for instance by methods slotNodeOpen, slotNodeClose).

        .. _Warning:

        Warning! Don\'t call this method until the GUI initialisation finishes.
        It will fail if it is invoqued before the required database is open.
        This is the reason why connectSignals() is called as late as possible
        in the constructor.

        :Parameter current: the model index of the current item
        """

        # The following actions are always active:
        # fileNew, fileOpen, fileOpenRO, fileExit and the Help menu actions

        # The set of actions that can be enabled or disabled
        actions = sets.Set(['fileClose', 'fileCloseAll', 'fileSaveAs', 
                            'nodeOpen', 'nodeClose', 'nodeProperties', 
                            'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy', 
                            'nodePaste', 'nodeDelete', 
                            'queryNew', 'queryDeleteAll'])
        enabled = sets.Set([])

        model_rows = self.dbs_tree_model.rowCount(QtCore.QModelIndex())
        if model_rows <=0:
            return

        # If there are open files aside the temporary DB
        if model_rows > 1:
            enabled = enabled.union(['fileCloseAll'])

        # if there are filtered tables --> queryDeleteAll is enabled
        tmp_index = self.dbs_tree_model.index(model_rows - 1, 0, 
            QtCore.QModelIndex())
        ftables = self.dbs_tree_model.rowCount(tmp_index)
        if ftables > 0:
            enabled = enabled.union(['queryDeleteAll'])

        current = self.dbs_tree_view.currentIndex()
        node = self.dbs_tree_model.nodeFromIndex(current)
        if node != self.dbs_tree_model.root:
            # Actions always enabled for every node
            enabled = enabled.union(['nodeProperties', 
                                     'nodeCopy'])

            # If the selected file is not the temporary DB
            if node.filepath != self.dbs_tree_model.tmp_filepath:
                enabled = enabled.union(['fileSaveAs', 'fileClose'])

            kind = node.node_kind
            # If the node is a table --> queryNew is enabled
            if kind == 'table':
                enabled = enabled.union(['queryNew'])

            # If the file is not open in read-only mode
            mode = self.dbs_tree_model.getDBDoc(node.filepath).mode
            if mode != 'r':
                if kind == 'root group':
                    enabled = enabled.union(['nodeNew', 'nodePaste'])
                elif kind == 'group':
                    enabled = enabled.union(['nodeNew', 'nodeRename', 
                                            'nodeCut', 'nodePaste', 
                                            'nodeDelete'])
                elif kind == 'table':
                    enabled = enabled.union(['nodeRename', 'nodeCut', 
                                            'nodeDelete'])
                else:
                    enabled = enabled.union(['nodeRename', 'nodeCut', 
                                            'nodeDelete'])

            if kind not in ('group', 'root group'):
                if node.has_view:
                    enabled = enabled.union(['nodeClose'])
                else:
                    enabled = enabled.union(['nodeOpen'])

        disabled = actions.difference(enabled)
        for action in enabled:
            self.gui_actions[action].setEnabled(True)
        for action in disabled:
            self.gui_actions[action].setDisabled(True)


    def updateRecentFiles(self, filepath, mode):
        """
        Add a new path to the list of most recently open files.

        ``processCommandLineArgs``, ``recoverLastSession``, ``slotFileNew``,
        and ``slotFileOpen`` call this method.

        :Parameters:

            - `filepath`: the last opened/created file
            - `mode`: the opening mode of the file
        """

        item = QtCore.QString('%1#@#%2').\
                                arg(mode).\
                                arg(vitables.utils.forwardPath(str(filepath)))

        # Updates the list of recently open files. Most recent goes first.
        if not self.recent_files.contains(item):
            self.recent_files.insert(0, item)
        else:
            self.recent_files.removeAt(self.recent_files.indexOf(item))
            self.recent_files.insert(0, item)
        while self.recent_files.count() > self.number_of_recent_files:
            self.recent_files.takeLast()


    def clearRecentFiles(self):
        """
        Clear the list of recently opened files and delete the corresponding
        historical file.
        """

        self.recent_files.clear()


    def slotUpdateRecentSubmenu(self):
        """Update the content of the Open Recent File submenu."""

        index = 0
        self.open_recent_submenu.clear()
        iconset = vitables.utils.getIcons()
        for item in self.recent_files:
            index += 1
            (mode, filepath) = str(item).split('#@#')
            action = QtGui.QAction('%s. %s' % (index, filepath), self)
            action.setData(QtCore.QVariant(item))
            self.connect(action, QtCore.SIGNAL("triggered()"), 
                self.openRecentFile)
            if mode == 'r':
                action.setIcon(iconset['file_ro'])
            else:
                action.setIcon(iconset['file_rw'])
            self.open_recent_submenu.addAction(action)

        # Always add a separator and a clear QAction. So if the menu is empty
        # the user still will know what's going on
        self.open_recent_submenu.addSeparator()
        action = QtGui.QAction(self.__tr('&Clear',
            'A recent submenu command'), self)
        self.connect(action, QtCore.SIGNAL("triggered()"), 
            self.clearRecentFiles)
        self.open_recent_submenu.addAction(action)


    def slotUpdateWindowsMenu(self):
        """
        Update the Windows menu.

        The Windows menu is dynamic because its content is determined
        by the currently open views. Because the number of these views or
        its contents may vary at any moment we must update the Windows
        menu every time it is open. For simplicity we don't keep track
        of changes in the menu content. Instead, we clean and create it
        from scratch every time it is about to show.
        """

        self.windows_menu.clear()
        windows_actions = ['windowCascade', 'windowTile', 
                           'windowRestoreAll', 'windowMinimizeAll', 
                           'windowClose', 'windowCloseAll', None]
        vitables.utils.addActions(self.windows_menu, windows_actions, 
                                    self.gui_actions)
        windows_list = self.workspace.subWindowList()
        if not windows_list:
            return
        self.windows_menu.setSeparatorsCollapsible(True)

        menu = self.windows_menu
        counter = 1
        for window in windows_list:
            title = window.windowTitle()
            if counter == 10:
                menu.addSeparator()
                menu = menu.addMenu(self.__tr("&More", 'A Windows submenu'))
            accel = ""
            if counter < 10:
                accel = "&%d " % counter
            elif i < 36:
                accel = "&%c " % chr(counter + ord("@") - 9)
            action = menu.addAction("%s%s" % (accel, title))
            action.setCheckable(True)
            if self.workspace.activeSubWindow() == window: action.setChecked(True)
            menu.action_group.addAction(action)
            self.connect(action, QtCore.SIGNAL("triggered()"), 
                        self.window_mapper, QtCore.SLOT("map()"))
            self.window_mapper.setMapping(action, window)
            counter = counter + 1
    def updateStatusBar(self):
        """Update the permanent message of the status bar.
        """

        current = self.dbs_tree_view.currentIndex()
        if current.isValid():
            tip = self.dbs_tree_model.data(current, QtCore.Qt.StatusTipRole)
            message = tip.toString()
        else:
            message = ''
        self.sb_node_info.setText(message)


    def popupContextualMenu(self, kind, pos):
        """
        Popup a contextual menu in the tree of databases view.

        When a point of the tree view is right clicked, a contextual
        popup is displayed. The content of the popup depends on the
        kind of node pointed: no node, root group, group or leaf.

        :Parameters:

            - `kind`: defines the content of the menu
            - `pos`: the clicked point in global coordinates
        """

        if kind == 'view':
            menu = self.view_cm
        elif kind == 'root group':
            menu = self.root_node_cm
        elif kind == 'group':
            menu = self.group_node_cm
        else:
            menu = self.leaf_node_cm
        menu.popup(pos)


    def closeChildrenViews(self, nodepath, filepath):
        """Close views being overwritten during node editing.

        :Parameters:

            - `nodepath`: the full path of the node that is overwrting other nodes
            - `filepath`: the full path of the file where that node lives
        """

        for window in self.workspace.subWindowList():
            wnodepath = window.leaf.nodepath
            wfilepath = window.leaf.filepath
            if not wfilepath == filepath:
                continue
            if wnodepath[0:len(nodepath)] == nodepath:
                window.close()

    def changeMDIViewMode(self):
        """Toggle the view mode of the workspace.
        """

        if self.workspace.viewMode() == QtGui.QMdiArea.SubWindowView:
            self.workspace.setViewMode(QtGui.QMdiArea.TabbedView)
        else:
            self.workspace.setViewMode(QtGui.QMdiArea.SubWindowView)
    def eventFilter(self, widget, event):
        """Event filter used to provide the MDI area with a context menu.

        :Parameters:
            -`widget`: the widget that receives the event
            -`event`: the event being processed
        """

        if widget == self.workspace:
            if event.type() == QtCore.QEvent.ContextMenu:
                pos = event.globalPos()
                self.mdi_cm.popup(pos)
            return QtGui.QMdiArea.eventFilter(widget, widget, event)
        else:
           return QtGui.QMainWindow.eventFilter(self, widget, event)


    def getFilepath(self, caption, accept_mode, file_mode, filepath=''):
        """Raise a file selector dialog and get a filepath.

        :Parameters:

        - `caption`: the dialog caption
        - `accept_mode`: the dialog accept mode
        - `file_mode`: the dialog file mode
        - `filepath`: the filepath initially selected
        """

        file_selector = QtGui.QFileDialog(self, 
                                    caption, 
                                    '', 
                                    self.__tr("""HDF5 Files (*.h5 *."""
                                    """hd5 *.hdf5);;All Files (*)""", 
                                    'Filter for the Open New dialog'))
        # Misc. setup
        if self.is_startup and self.startup_working_directory == 'home':
            self.is_startup = False
            self.last_working_directory = vitables.utils.getHomeDir()
        file_selector.setDirectory(self.last_working_directory)
        file_selector.setAcceptMode(accept_mode)
        if accept_mode == QtGui.QFileDialog.AcceptSave:
            file_selector.setConfirmOverwrite(False)
        file_selector.setFileMode(file_mode)
        file_selector.setHistory(self.file_selector_history)
        if filepath:
            file_selector.selectFile(filepath)

        # Execute the dialog
        try:
            if file_selector.exec_():  # OK clicked
                filepath = file_selector.selectedFiles()[0]
                # Update the working directory
                self.last_working_directory = \
                    str(file_selector.directory().canonicalPath())
                # Update the history
                if not file_selector.history().contains(\
                                                self.last_working_directory):
                    self.file_selector_history.append(\
                                                self.last_working_directory)
            else:  # Cancel clicked
                filepath = QtCore.QString('')
        finally:
            del file_selector
        return str(filepath)


    def checkFileExtension(self, filepath):
        """
        Check the filename extension of a given file.

        If the filename has no extension this method adds .h5
        extension to it. This is useful when a file is being created or
        saved.

        :Parameter filepath: the full path of the file (a QString)

        :Returns: the filepath with the proper extension (a Python string)
        """

        filepath = unicode(filepath)
        if not re.search('\.(.+)$', os.path.basename(filepath)):
            ext = '.h5'
            filepath = '%s%s' % (filepath, ext)
        return filepath


    def slotFileNew(self):
        """Create a new file."""

        filepath = self.getFilepath(
            self.__tr('Creating a new file...', 
                      'Caption of the File New... dialog'), 
            QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.AnyFile)

        if not filepath:
            # The user has canceled the dialog
            return

        # Make sure the path is not a relative path and contains no
        # backslashes
        filepath = QtCore.QDir.fromNativeSeparators(os.path.abspath(filepath))
        filepath = unicode(filepath)

        # Check the file extension
        filepath = self.checkFileExtension(filepath)

        # Check the returned path
        if os.path.exists(filepath):
            print self.__tr(
                """\nWarning: """
                """new file creation failed because file already exists.""",
                'A file creation error')
            return

        # Create the pytables file and close it.
        db_doc = self.dbs_tree_model.createDBDoc(filepath)
        if db_doc:
            # The write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            self.updateRecentFiles(filepath, 'a')


    def slotFileSaveAs(self):
        """
        Save a renamed copy of a file.

        This method exhibits the typical behavior: copied file is closed
        and the fresh renamed copy is open.
        """

        overwrite = False
        current_index = self.dbs_tree_view.currentIndex()

        # The file being saved
        initial_filepath = \
            self.dbs_tree_model.nodeFromIndex(current_index).filepath
        initial_dirname, initial_filename = os.path.split(initial_filepath)

        # The trier filepath
        trier_filepath = self.getFilepath(
            self.__tr('Copying a file...', 
                      'Caption of the File Save as... dialog'), 
            QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.AnyFile, 
            initial_filepath)
        if not trier_filepath:  # The user has canceled the dialog
            return

        # Make sure the path is not a relative path and contains no
        # backslashes
        trier_filepath = \
            QtCore.QDir.fromNativeSeparators(os.path.abspath(trier_filepath))
        trier_filepath = unicode(trier_filepath)

        trier_filepath = self.checkFileExtension(trier_filepath)

        #
        # Check if the chosen name is valid
        #

        info = [self.__tr('File Save as: file already exists', 
                'A dialog caption'), None]
        # Bad filepath conditions
        trier_dirname, trier_filename = os.path.split(trier_filepath)
        sibling = os.listdir(trier_dirname)
        filename_in_sibling = trier_filename in sibling
        is_tmp_filepath = trier_filepath == self.dbs_tree_model.tmp_filepath
        is_initial_filepath = trier_filepath == initial_filepath

        # If the suggested filepath is not valid ask for a new filepath
        # The loop is necessary because the file being saved as and the
        # temporary database can be in the same directory. In this case
        # we must check all error conditions every time a new name is tried
        while is_tmp_filepath or is_initial_filepath or filename_in_sibling:
            if is_tmp_filepath:
                info[1] = self.__tr("""Target directory: %s\n\nThe Query """
                                """results database cannot be overwritten.""", 
                                'Overwrite file dialog label') % trier_dirname
                pattern = \
                    "(^%s$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$" \
                    % trier_filename
                dialog = renameDlg.RenameDlg(trier_filename, pattern, info)
            elif is_initial_filepath:
                info[1] = self.__tr("""Target directory: %s\n\nThe file """
                                """being saved cannot overwrite itself.""", 
                                'Overwrite file dialog label') % trier_dirname
                pattern = \
                    "(^%s$)|[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$" \
                    % trier_filename
                dialog = renameDlg.RenameDlg(trier_filename, pattern, info)
            elif filename_in_sibling:
                info[1] = self.__tr("""Target directory: %s\n\nFile name """
                    """'%s' already in use in that directory.\n""", 
                    'Overwrite file dialog label') % (trier_dirname, 
                    trier_filename)
                pattern = "[a-zA-Z_]+[0-9a-zA-Z_]*(?:\.[0-9a-zA-Z_]+)?$"
                dialog = renameDlg.RenameDlg(trier_filename, pattern, info)
            if dialog.exec_():
                trier_filename = dialog.action['new_name']
                trier_filepath = os.path.join(trier_dirname, trier_filename)
                trier_filepath = \
                    QtCore.QDir.fromNativeSeparators(trier_filepath)
                overwrite = dialog.action['overwrite']
                # Update the error conditions
                is_initial_filepath = trier_filepath == initial_filepath
                is_tmp_filepath = \
                    trier_filepath == self.dbs_tree_model.tmp_filepath
                filename_in_sibling = trier_filename in sibling
                del dialog
                if (overwrite == True) and (not is_initial_filepath) and \
                    (not is_tmp_filepath):
                    break
            else:
                del dialog
                return

        filepath = self.checkFileExtension(trier_filepath)

        # If an open file is overwritten then close it
        if overwrite and self.dbs_tree_model.getDBDoc(filepath):
            for row, child in enumerate(self.dbs_tree_model.root.children):
                if child.filepath == filepath:
                    self.slotFileClose(self.dbs_tree_model.index(row, 0, 
                                                        QtCore.QModelIndex()))
            # The current index could have changed when overwriting
            # so we update it
            for row in range(0, self.dbs_tree_model.rowCount(QtCore.QModelIndex())):
                index = QtCore.QModelIndex().child(row, 0)
                node = self.dbs_tree_model.nodeFromIndex(index)
                if node.filepath == initial_filepath:
                    current_index = index
            self.dbs_tree_view.setCurrentIndex(current_index)

        # Make a copy of the selected file
        try:
            QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            dbdoc = self.dbs_tree_model.getDBDoc(initial_filepath)
            dbdoc.copyFile(filepath)
        finally:
            QtGui.qApp.restoreOverrideCursor()

        # Close the copied file (which is selected in the tree view) and
        # open the new copy in read-write mode. The position in the tree
        # is kept but it should never be the last position (ViTables assumes
        # that the temporary database has always the last position).
        # If a file has been closed in the Save As process then we have to
        # check that the position is not the last one.
        position = current_index.row()
        if position == self.dbs_tree_model.rowCount(QtCore.QModelIndex()) - 1:
            position = position - 1
        self.slotFileClose()
        self.slotFileOpen(QtCore.QString(filepath), 'a', position) 


    def slotFileOpenRO(self, filepath=None):
        """
        Open a file that contains a ``PyTables`` database in read-only mode.

        :Parameters filepath: the full path of the file to be open
        """
        self.slotFileOpen(filepath, mode='r')


    def openRecentFile(self):
        """
        Opens the file whose path appears in the activated menu item text.
        """

        action = self.sender()
        item = action.data().toString()
        (mode, filepath) = str(item).split('#@#')
        self.slotFileOpen(filepath, str(mode))


    def slotFileOpen(self, filepath=None, mode='a', position=0):
        """
        Open a file that contains a ``PyTables`` database.

        If this method is invoqued via ``File -> Open`` then no filepath
        is passed and a dialog is raised. When the method is invoqued
        via slotRecentSubmenuActivated or slotFileSaveAs methods then
        filepath is passed and the dialog is not raised.

        :Parameters:

            - `filepath`: the full path of the file to be open
            - `mode`: the file opening mode. It can be read-write or read-only
        """

        if not filepath:
            filepath = self.getFilepath(self.__tr('Select a file for opening', 
                                        'Caption of the File Open... dialog'), 
                                        QtGui.QFileDialog.AcceptOpen, 
                                        QtGui.QFileDialog.ExistingFile)
            if not filepath:
                # The user has canceled the dialog
                return
        else:
            # Make sure the path is not a relative path and contains no
            # backslashes
            filepath = \
                QtCore.QDir.fromNativeSeparators(os.path.abspath(filepath))
            filepath = unicode(filepath)


        # Open the database and select it in the tree view
        self.dbs_tree_model.openDBDoc(filepath, mode, position)
        database = self.dbs_tree_model.getDBDoc(filepath)
        if database:
            self.dbs_tree_view.setCurrentIndex(self.dbs_tree_model.index(position, 
                0, QtCore.QModelIndex()))
            self.updateRecentFiles(filepath, mode)


    def slotFileClose(self, current=None):
        """
        Close a file.

        First of all this method finds out which database it has to close.
        Afterwards all views belonging to that database are closed, then
        the object tree is removed from the QListView and, finally, the
        database is closed.

        current: the index of a node living in the file being closed
        """

        if not current:
            current = self.dbs_tree_view.currentIndex()
        filepath = self.dbs_tree_model.nodeFromIndex(current).filepath

        # If some leaf of this database has an open view then close it
        for window in self.workspace.subWindowList():
            if window.leaf.filepath == filepath:
                window.close()

        # The tree model closes the file and delete its root item
        # from the tree view
        self.dbs_tree_model.closeDBDoc(filepath)


    def slotFileCloseAll(self):
        """Close every file opened by user."""

        # The list of top level items to be removed.
        # The temporary database should be closed at quit time only
        open_files = len(self.dbs_tree_model.root.children) - 1
        rows_range = range(0, open_files)
        # Reversing is a must because, if we start from 0, row positions
        # change as we delete rows
        rows_range.reverse()
        for row in rows_range:
            index = self.dbs_tree_model.index(row, 0, QtCore.QModelIndex())
            self.slotFileClose(index)


    def slotFileExit(self):
        """
        Safely closes the application.

        Save current configuration on disk, closes opened files and exits.
        """

        # Close all browsers
        while len(self.doc_browsers) > 0:
            self.doc_browsers[0].slotExitBrowser()
        # Save current configuration
        self.saveConfiguration()
        # Close every user opened file
        self.slotFileCloseAll()
        # Close the temporary database
        index = self.dbs_tree_model.index(0, 0, QtCore.QModelIndex())
        self.slotFileClose(index)
        # Application quit
        QtGui.qApp.quit()


    def slotNodeOpen(self, current=None):
        """
        Opens a leaf node for viewing.

        :Parameter current: the model index of the item to be opened
        """

        if current is None:
            index = self.dbs_tree_view.currentIndex()
        else:
            index = current
        pindex = QtCore.QPersistentModelIndex(index)
        dbs_tree_leaf = self.dbs_tree_model.nodeFromIndex(index)
        leaf = dbs_tree_leaf.node # A PyTables node

        # The buffer tied to this node in order to optimize the read access
        leaf_buffer = rbuffer.Buffer(leaf)

        # tables.UnImplemented datasets cannot be read so are not opened
        if isinstance(leaf, tables.UnImplemented):
            info_box = QtGui.QMessageBox.information(self, 
                self.__tr('About UnImplemented nodes', 'A dialog caption'), 
                self.__tr(
                """Actual data for this node are not accesible.<br> """
                """The combination of datatypes and/or dataspaces in this """
                """node is not yet supported by PyTables.<br>"""
                """If you want to see this kind of dataset implemented in """
                """PyTables, please, contact the developers.""",
                'Text of the Unimplemented node dialog'))
            return

        # Leaves that cannot be read are not opened
        if not leaf_buffer.isDataSourceReadable():
            return

        # Create a model and a view for the leaf
        leaf_model = leafModel.LeafModel(leaf_buffer)
        leaf_view = leafView.LeafView(leaf_model)

        # Add the view to the MDI area
        subwindow = dataSheet.DataSheet(dbs_tree_leaf, leaf_view, pindex, self)
        self.workspace.addSubWindow(subwindow)
        subwindow.show()


    def slotNodeClose(self, current=None):
        """
        Closes the view of the selected node.

        The method is called by activating ``Node --> Close`` (what passes
        no argument) or programatically by the ``VTApp.slotFileClose()``
        method (what does pass argument).
        If the target is an open leaf this method closes its view, delete
        its model and updates the controller tracking system.
        If the target node is a root group the method looks for opened
        children and closes them as described above.

        :Parameter current: the tree view item to be closed
        """

        index = self.dbs_tree_view.currentIndex()
        dbs_tree_leaf = self.dbs_tree_model.nodeFromIndex(index)

        # Find out the subwindow tied to the selected node and close it
        for subwindow in self.workspace.subWindowList():
            if subwindow.leaf == dbs_tree_leaf:
                subwindow.close()


    def slotNodeNewGroup(self):
        """Create a new group node."""

        current = self.dbs_tree_view.currentIndex()
        parent = self.dbs_tree_model.nodeFromIndex(current)

        # Get the new group name
        dialog = inputNodeName.InputNodeName(\
            self.__tr('Creating a new group', 'A dialog caption'), 
            self.__tr('Source file: %s\nParent group: %s\n\n ', 
                'A dialog label') % (parent.filepath, parent.nodepath), 
            self.__tr('Create', 'A button label'))
        if dialog.exec_():
            suggested_nodename = dialog.node_name
            del dialog
        else:
            del dialog
            return

        #
        # Check if the entered nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        info = [self.__tr('Creating a new group: name already in use', 
                'A dialog caption'), 
                self.__tr("""Source file: %s\nParent group: %s\n\nThere is """
                          """already a node named '%s' in that parent group.\n""", 
                          'A dialog label') % \
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename, sibling, 
            pattern, info)
        if nodename is None:
            return

        # If the creation overwrites a group with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.closeChildrenViews(nodepath, parent.filepath)

        self.dbs_tree_model.createGroup(current, nodename, overwrite)

    def slotNodeRename(self):
        """
        Rename the selected node.

        - ask for the node name
        - check the node name. If it is already in use ask what to<br>
          do (possibilities are rename, overwrite and cancel creation)
        - rename the node
        """

        index = self.dbs_tree_view.currentIndex()
        child = self.dbs_tree_model.nodeFromIndex(index)
        parent = child.parent

        # Get the new nodename
        dialog = inputNodeName.InputNodeName(\
            self.__tr('Renaming a node', 'A dialog caption'),
            self.__tr('Source file: %s\nParent group: %s\n\n', 
                    'A dialog label') % (parent.filepath, parent.nodepath), 
            self.__tr('Rename', 'A button label'))
        if dialog.exec_():
            suggested_nodename = dialog.node_name
            del dialog
        else:
            del dialog
            return

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Note that current nodename is not allowed as new nodename.
        # Embedding it in the pattern makes unnecessary to pass it to the
        # rename dialog via method argument and simplifies the code
        pattern = """(^%s$)|""" \
            """(^[a-zA-Z_]+[0-9a-zA-Z_ ]*)""" % child.name
        info = [self.__tr('Renaming a node: name already in use', 
                'A dialog caption'), 
                self.__tr("""Source file: %s\nParent group: %s\n\nThere is """
                          """already a node named '%s' in that parent group.\n""", 
                          'A dialog label') % \
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename, sibling, 
            pattern, info)
        if nodename is None:
            return

        # If the renaming overwrites a node with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.closeChildrenViews(nodepath, child.filepath)

        # Rename the node
        self.dbs_tree_model.renameNode(index, nodename, overwrite)

        # Update the Selected node indicator of the status bar
        self.updateStatusBar()

    def slotNodeCut(self):
        """Cut the selected node."""

        current = self.dbs_tree_view.currentIndex()

        # If the cut node has attached views then these views are closed
        # before the cutting is done. This behavior can be inconvenient
        # for users but get rid of potential problems that arise if, for
        # any reason, the user doesn't paste the cut node.
        node = self.dbs_tree_model.nodeFromIndex(current)
        self.closeChildrenViews(node.nodepath, node.filepath)

        # Cut the node
        self.dbs_tree_model.cutNode(current)

    def slotNodeCopy(self):
        """
        Copy the selected node.
        """

        current = self.dbs_tree_view.currentIndex()

        # Non readable leaves should not be copied
        dbs_tree_node = self.dbs_tree_model.nodeFromIndex(current)
        if not (dbs_tree_node.node_kind in ('root group', 'group')):
            leaf = dbs_tree_node.node # A PyTables node
            leaf_buffer = rbuffer.Buffer(leaf)
            if not leaf_buffer.isDataSourceReadable():
                info_box = QtGui.QMessageBox.information(self, 
                    self.__tr('About unreadable datasets', 'A dialog caption'), 
                    self.__tr(
                    """Sorry, actual data for this node are not accesible.<br>"""
                    """The node will not be copied.""", 
                    'Text of the Unimplemented node dialog'))
                return

        # Copy the node
        self.dbs_tree_model.copyNode(current)


    def slotNodePaste(self):
        """
        Paste the currently copied/cut node under the selected node.
        """

        current = self.dbs_tree_view.currentIndex()
        parent = self.dbs_tree_model.nodeFromIndex(current)
        copied_node = self.dbs_tree_model.copied_node_info
        if copied_node == {}:
            return
        if copied_node['nodepath'] == '/':
            nodename = 'root_group_of_%s' \
                        % os.path.basename(copied_node['filepath'])
        else:
            nodename = os.path.basename(copied_node['nodepath'])

        # Check if pasting is allowed. It is not when the node has been
        # copied and
        # - source and target are the same node
        # - target is the source's parent
        # Pasting cut nodes has no restrictions
        if (copied_node['is_copied'] == True) and \
           (copied_node['filepath'] == parent.filepath):
            if (copied_node['nodepath'] == parent.nodepath) or \
               (parent.nodepath == copied_node['parent_nodepath']):
                return

        #
        # Check if the nodename is already in use
        #
        sibling = getattr(parent.node, '_v_children').keys()
        # Nodename pattern
        pattern = "[a-zA-Z_]+[0-9a-zA-Z_ ]*"
        # Bad nodename conditions
        nodename_in_sibling = nodename in sibling
        info = [self.__tr('Node paste: nodename already exists', 
                'A dialog caption'), 
                self.__tr("""Source file: %s\nCopied node: %s\n"""
                    """Destination file: %s\nParent group: %s\n\n"""
                    """Node name '%s' already in use in that group.\n""", 
                    'A dialog label') % \
                    (copied_node['filepath'], copied_node['nodepath'], 
                    parent.filepath, parent.nodepath, nodename), 
                self.__tr('Paste', 'A button label')]
        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(nodename, sibling, 
            pattern, info)
        if nodename is None:
            return

        # If the pasting overwrites a node with attached views then these
        # views are closed before the pasting is done
        if overwrite:
            nodepath = tables.path.joinPath(parent.nodepath, nodename)
            self.closeChildrenViews(nodepath, parent.filepath)

        # Paste the node
        self.dbs_tree_model.pasteNode(current, nodename, overwrite)

    def slotNodeDelete(self, current=None, force=None):
        """
        Delete a given node.

        :Parameters;

            - `force`: ask/do not ask for confirmation before deletion
        """

        if current is None:
            current = self.dbs_tree_view.currentIndex()
        node = self.dbs_tree_model.nodeFromIndex(current)

        # Confirm deletion dialog
        if not force:
            del_dlg = QtGui.QMessageBox.question(self,
                self.__tr('Node deletion',
                'Caption of the node deletion dialog'),
                self.__tr("""\nYou are about to delete the node:\n%s\n""",
                'Ask for confirmation') % node.nodepath,
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.Default,
                QtGui.QMessageBox.No|QtGui.QMessageBox.Escape)

            # OK returns Accept, Cancel returns Reject
            if del_dlg == QtGui.QMessageBox.No:
                return

        # If item is a filtered table then update the list of used names
        if hasattr(node.node._v_attrs, 'query_condition'):
            self.queries_mgr.ft_names.remove(node.name)

        # If the deletion involves a node with attached views then these
        # views are closed before the deletion is done
        self.closeChildrenViews(node.nodepath, node.filepath)

        # Delete the node
        self.dbs_tree_model.deleteNode(current)

        # Synchronise the workspace with the tree of databases pane i.e.
        # ensure that the new current node (if any) gets selected
        select_model = self.dbs_tree_view.selectionModel()
        new_current = self.dbs_tree_view.currentIndex()
        select_model.select(new_current, QtGui.QItemSelectionModel.Select)

    def slotNodeProperties(self):
        """
        Display the properties dialog for the currently selected node.

        The method is called by activating Node --> Properties.
        """

        current = self.dbs_tree_view.currentIndex()
        node = self.dbs_tree_model.nodeFromIndex(current)
        info = nodeInfo.NodeInfo(node)
        nodePropDlg.NodePropDlg(info)


    def slotQueryNew(self):
        """
        Add a new filtered table item to the query results tree.

        The creation process has 2 steps:

        - create the filtered table in the temporary database
        - add the filtered table to the Query results tree in the tree pane

        Finally the filtered table is opened.
        """

        current = self.dbs_tree_view.currentIndex()
        node = self.dbs_tree_model.nodeFromIndex(current)

        # The updateQueryActions method ensures that the current node is
        # tied to a tables.Table instance so we can query it without
        # further checking
        table = \
            self.dbs_tree_model.getDBDoc(node.filepath).getNode(node.nodepath)
        info = self.queries_mgr.getQueryInfo(table)
        if info is None:
            return

        ft_name = self.queries_mgr.queryTable(table, info[0], info[1])

        if ft_name:
            # Update temporary database view i.e. call lazyAddChildren
            model_rows = self.dbs_tree_model.rowCount(QtCore.QModelIndex())
            tmp_index = self.dbs_tree_model.index(model_rows - 1, 0, 
                QtCore.QModelIndex())
            self.dbs_tree_model.lazyAddChildren(tmp_index)
            # The new filtered table is inserted in first position under
            # the Query results node
            index = self.dbs_tree_model.index(0, 0, tmp_index)
            self.slotNodeOpen(index)


    def slotQueryDeleteAll(self):
        """Delete all nodes from the query results tree."""

        del_dlg = QtGui.QMessageBox.question(self,
            self.__tr('Deleting all queries',
            'Caption of the QueryDeleteAll dialog'),
            self.__tr("""\n\nYou are about to delete all nodes """
                """under Query results\n\n""", 'Ask for confirmation'),
            QtGui.QMessageBox.Yes|QtGui.QMessageBox.Default,
            QtGui.QMessageBox.No|QtGui.QMessageBox.Escape)

        # OK returns Accept, Cancel returns Reject
        if del_dlg == QtGui.QMessageBox.No:
            return

        # Remove every filtered table from the tree of databases model/view
        model_rows = self.dbs_tree_model.rowCount(QtCore.QModelIndex())
        tmp_index = self.dbs_tree_model.index(model_rows - 1, 0, 
            QtCore.QModelIndex())
        rows_range = range(0, self.dbs_tree_model.rowCount(tmp_index))
        rows_range.reverse()
        for row in rows_range:
            index = self.dbs_tree_model.index(row, 0, tmp_index)
            self.slotNodeDelete(index, force=True)

        # Reset the queries manager
        self.queries_mgr.counter = 0
        self.queries_mgr.ft_names = []


    def slotWindowsClose(self):
        """Close the window currently active in the workspace."""
        self.workspace.activeSubWindow().close()

    def slotWindowsCloseAll(self):
        """Close all open windows."""

        for window in self.workspace.subWindowList():
            window.close()

    def slotWindowsRestoreAll(self):
        """Restore every window in the workspace to its normal size."""

        for window in self.workspace.subWindowList():
            window.showNormal()
    def slotWindowsMinimizeAll(self):
        """Restore every window in the workspace to its normal size."""

        for window in self.workspace.subWindowList():
            window.showMinimized()
    def slotToolsPreferences(self):
        """
        Launch the Preferences dialog.

        Clicking the ``OK`` button applies the configuration set in the
        Preferences dialog.
        """

        prefs =  preferences.Preferences(self)
        try:
            if prefs.gui.exec_() == QtGui.QDialog.Accepted:
                self.loadConfiguration(prefs.new_prefs)
        finally:
            del prefs


    def slotHelpDocBrowser(self):
        """
        Open the documentation browser

        Help --> UsersGuide
        """

        browser = helpBrowser.HelpBrowser(self)
        self.doc_browsers.append(browser)


    def slotHelpAbout(self):
        """
        Show a tabbed dialog with the application About and License info.

        Help --> About
        """

        # Text to be displayed
        about_text = self.__tr(
            """<qt>
            <h3>ViTables %s</h3>
            ViTables is a graphical tool for displaying datasets
            stored in PyTables and HDF5 files. It is written using PyQt
            , the Python bindings for the Qt GUI toolkit.<p>
            For more information see
            <b>http://www.vitables.org</b>.<p>
            Please send bug reports or feature requests to the
            <em>ViTables Users Group</em>.<p>
            ViTables uses third party software which is copyrighted by
            its respective copyright holder. For details see the
            copyright notice of the individual packages.
            </qt>""",
            'Text of the About ViTables dialog')  % vtconfig.getVersion()
        license_text = vitables.utils.getLicense()

        # Construct the dialog
        about_dlg = QtGui.QDialog(self)
        about_dlg.setWindowTitle(self.__tr('About ViTables %s',
            'Caption of the About ViTables dialog') % vtconfig.getVersion())
        layout = QtGui.QVBoxLayout(about_dlg)
        tab_widget = QtGui.QTabWidget(about_dlg)
        buttons_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        layout.addWidget(tab_widget)
        layout.addWidget(buttons_box)

        self.connect(buttons_box, QtCore.SIGNAL("accepted()"), about_dlg, 
            QtCore.SLOT("accept()"))

        # Make About page
        about_page = QtGui.QWidget()
        about_page.setLayout(QtGui.QVBoxLayout())
        about_edit = QtGui.QTextEdit(about_page)
        about_edit.setReadOnly(1)
        about_edit.setAcceptRichText(True)
        about_edit.setText(about_text)
        about_page.layout().addWidget(about_edit)
        tab_widget.addTab(about_page, self.__tr('&About...',
            'Title of the first tab of the About dialog'))

        # Make License page
        license_page = QtGui.QWidget()
        license_page.setLayout(QtGui.QVBoxLayout())
        license_edit = QtGui.QTextEdit(license_page)
        license_edit.setReadOnly(1)
        license_edit.setAcceptRichText(True)
        license_edit.setText(license_text)
        license_page.layout().addWidget(license_edit)
        tab_widget.addTab(license_page, self.__tr('&License',
            'Title of the second tab of the About dialog'))

        # Show the dialog
        about_dlg.exec_()


    def slotHelpAboutQt(self):
        """
        Shows a message box with the Qt About info.

        Help --> About Qt
        """

        QtGui.QMessageBox.aboutQt(self, self.__tr('About Qt',
            'Caption of the About Qt dialog'))


    def slotHelpVersions(self):
        """
        Message box with info about versions of libraries used by
        ViTables.

        Help --> Show Versions
        """

        # The libraries versions dictionary
        libs_versions = {
            'title': self.__tr('Version Numbers',
                'Caption of the Versions dialog'),
            'Python': reduce(lambda x,y: '.'.join([str(x), str(y)]),
                sys.version_info[:3]),
            'PyTables': tables.__version__ ,
            'NumPy': tables.numpy.__version__,
            'Qt': QtCore.qVersion(),
            'PyQt': QtCore.PYQT_VERSION_STR,
            'ViTables': vtconfig.getVersion()
        }

        # Add new items to the dictionary
        libraries = ('HDF5', 'Zlib', 'LZO', 'BZIP2')
        for lib in libraries:
            lversion = tables.whichLibVersion(lib.lower())
            if lversion:
                libs_versions[lib] = lversion[1]
            else:
                libs_versions[lib] = self.__tr('not available',
                    'Part of the library not found text')

        # Construct the dialog
        versions_dlg = QtGui.QDialog(self)
        versions_dlg.setWindowTitle(self.__tr('Version Numbers', 
                                             'Caption of the Versions dialog'))
        layout = QtGui.QVBoxLayout(versions_dlg)
        versions_edit = QtGui.QTextEdit(versions_dlg)
        buttons_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        layout.addWidget(versions_edit)
        layout.addWidget(buttons_box)

        self.connect(buttons_box, QtCore.SIGNAL("accepted()"), versions_dlg, 
            QtCore.SLOT("accept()"))

        versions_edit.setReadOnly(1)
        versions_edit.setText(\
            """
            <qt>
            <h3>%(title)s</h3><br>
            <table>
            <tr><td><b>Python</b></td><td>%(Python)s</td></tr>
            <tr><td><b>PyTables</b></td><td>%(PyTables)s</td></tr>
            <tr><td><b>NumPy</b></td><td>%(NumPy)s</td></tr>
            <tr><td><b>HDF5</b></td><td>%(HDF5)s</td></tr>
            <tr><td><b>Zlib</b></td><td>%(Zlib)s</td></tr>
            <tr><td><b>LZO</b></td><td>%(LZO)s</td></tr>
            <tr><td><b>BZIP2</b></td><td>%(BZIP2)s</td></tr>
            <tr><td><b>Qt</b></td><td>%(Qt)s</td></tr>
            <tr><td><b>PyQt</b></td><td>%(PyQt)s</td></tr>
            <tr><td><b>ViTables</b></td><td>%(ViTables)s</td></tr>
            </table>
            </qt>""" % libs_versions)

        # Show the dialog
        versions_dlg.exec_()

