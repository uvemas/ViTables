# -*- coding: utf-8 -*-

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
#       $Id: vtapp.py 1020 2008-03-28 16:41:24Z vmas $
#
########################################################################

"""
Here is defined the VTApp class.

Classes:

* VTApp(qt.QObject)

Methods:

* __init__(self, mode='', dblist='', h5files=[], keep_splash=True, *args)
* __tr(self, source, comment=None)
* readConfiguration(self)
* connectSignals(self)
* slotUpdateSBNodeInfo(self)
* slotUpdateActions(self, window=None)
* synchronizeWorkspace(self)
* updateFileActions(self, selected=None, top=None)
* updateNodeActions(self, selected=None, top=None)
* updateQueryActions(self, selected=None, top=None)
* initSettings(self, current_config)
* updateRecentFiles(self, filePath, mode)
* recoverLastSession(self)
* processCommandLineArgs(self, mode='', h5files=[], dblist='')
* openFileDlg(self, name, mode, caption, new_file=False)
* checkFileExtension(self, filePath)
* slotFileNew(self)
* slotFileSaveAs(self)
* slotFileOpen(self, filePath=None, mode='a')
* slotFileClose(self, current=None, update=True)
* slotFileCloseAll(self,)
* slotFileExit(self)
* slotRecentSubmenuAboutToShow(self)
* openRecentFile(self, itemID)
* clearRecentFiles(self)
* slotNodeOpen(self, current=None)
* slotNodeClose(self, current=None)
* slotNodeNewGroup(self)
* slotNodeCut(self)
* slotNodeCopy(self)
* slotNodePaste(self, target=None)
* dropNode(self, source, target)
* slotNodeRename(self, inplace=False)
* slotNodeDelete(self, lvitem=None, force=None)
* slotNodeProperties(self)
* slotContextualNodeMenu(self, item, point, column)
* slotQueryNew(self)
* slotQueryList(self)
* slotQueryDeleteAll(self)
* slotWindowsMenuAboutToShow(self)
* activateWindow(self, index)
* raiseView(self, view)
* slotSynchronizeTreeView(self, active_window)
* slotWindowsClose(self)
* slotWindowsCloseAll(self)
* slotToolsLineUp(self)
* slotToolsHideToolBar(self)
* slotToolsPreferences(self)
* getPreferences(self)
* applyPreferences(self, preferences)
* getConfiguration(self)
* saveConfiguration(self)
* getSessionFilesNodes(self)
* slotHelpDocBrowser(self)
* slotHelpAbout(self)
* slotHelpAboutQt(self)
* slotHelpVersions(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys
import os
import time
import re

import tables
import qt
from qttable import QTable

import vitables.utils
import vitables.vtgui
import vitables.vtsplash
from  vitables.preferences import vtconfig
from vitables.h5db import dbManager
from vitables.nodes import leavesManager
from  vitables.preferences import preferences
from vitables.treeEditor import treeView
from vitables.docBrowser import helpBrowser
from vitables.vtTables import hpTable

class VTApp(qt.QObject):
    """
    The application core.

    It handles the user input and controls both views and documents.
    VTApp methods can be grouped as:

    * GUI initialization and configuration methods
    * slots that handle user input
    """


    def __init__(self, mode='', dblist='', h5files=[], keep_splash=True):
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

        qt.QObject.__init__(self)

        # The startup application flag for Open File dialogs
        self.isStartup = True
        # Instantiate a configurator object for the application
        self.config = vtconfig.Config()
        # List of HelpBrowser instances in memory
        self.docBrowsers = []

        # Show a splash screen
        imagesDir = self.config.icons_dir
        logo = qt.QPixmap("%s/vitables_logo.png" % imagesDir)
        splash = vitables.vtsplash.VTSplash(logo)
        splash.show()
        t0 = time.time()

        #
        # Make the GUI
        #
        splash.message(self.__tr('Creating the GUI...',
            'A splash screen message'))
        self.gui = vitables.vtgui.VTGUI(self)
        self.logger = self.gui.logger
        self.workspace = self.gui.workspace
        self.otLV = self.gui.otLV
        self.paste_disabled_item = None

        # Redirect standard output and standard error to a Logger instance
        sys.stdout = self.logger
        sys.stderr = self.logger

        # Print the welcome message
        print self.__tr('''ViTables %s\nCopyright (c) 2008 by Vicent Mas'''
            '''\nAll rights reserved.''' % vtconfig.getVersion(),
            'Application startup message')

        # Create managers for database objects and node objects
        self.leavesManager = leavesManager.LeavesManager(self)
        self.dbManager = dbManager.DBManager(self.gui)
        self.queryRoot = treeView.findTreeItem(self.otLV,
            self.dbManager.tmp_filepath, '/')

        # Apply the configuration stored on disk
        splash.message(self.__tr('Configuration setup...',
            'A splash screen message'))
        config = self.readConfiguration()
        self.initSettings(config)

        # Make sure that the splash screen is shown at least for two seconds
        if keep_splash:
            tf = time.time()
            while tf - t0 < 2:
                tf = time.time()
            splash.finish(self.gui)
            del splash

        # Once the splash is hidden and BEFORE showing the main window
        # the geometry of the last session is recovered
        [x, y, width, height] = config['Geometry/position']
        pos = qt.QPoint(x, y)
        size = qt.QSize(width, height)
        self.gui.resize(size)
        self.gui.move(pos)
        self.gui.show()
        self.gui.workspace.cascade()

        # Ensure that QActions have a consistent state
        self.connectSignals()
        self.slotUpdateActions()

        # The list of most recently open DBs
        self.numberOfRecentFiles = 10
        if len(self.recentFilesList) > self.numberOfRecentFiles:
            del self.recentFilesList[self.numberOfRecentFiles:]

        # Restore last session
        if self.restore_last_session:
            self.recoverLastSession()
        # Process the command line
        if h5files:
            self.processCommandLineArgs(mode=mode, h5files=h5files)
        elif dblist:
            self.processCommandLineArgs(dblist=dblist)
        # Synchronize workspace and tree view
        self.slotSynchronizeTreeView(self.gui.workspace.activeWindow())


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('VTApp', source, comment).latin1()


    def readConfiguration(self):
        """
        Get the application configuration currently stored on disk.

        Read the configuration from the stored settings. If a setting
        cannot be read (as it happens when the package is just
        installed) then its default value is returned.
        Geometry and Recent settings are returned as lists, color
        settings as QColor instances. The rest of settings are returned
        as QStrings or integers.

        This method is called when the application is configured for
        the very first time.

        :Returns: a dictionary with the configuration stored on disk
        """

        # We read the configuration in two steps: first the preferences,
        # then the rest of settings
        config = {}
        base_key = self.config.base_key
        subkeys = ['Logger/paper', 'Logger/text', 'Logger/font', 
            'Workspace/background', 'Look/currentStyle', 
            'Startup/startupWorkingDirectory', 'Startup/restoreLastSession', 
            'Geometry/position', 'Geometry/hsplitter', 
            'Geometry/vsplitter', 'Startup/lastWorkingDirectory', 
            'Recent/files', 'Session/files', 'HelpBrowser/bookmarks', 
            'HelpBrowser/history']
        lookEntry = self.config.entryList('%s/Look' % base_key)
        if not lookEntry:  # Settings are not yet stored on disk
            for key in subkeys:
                config[key] = self.config.confDef[key]
        else:
            # Logger
            config['Logger/paper'] = self.config.readLoggerPaper()
            config['Logger/text'] = self.config.readLoggerText()
            config['Logger/font'] = self.config.readLoggerFont()
            # Workspace
            config['Workspace/background'] = self.config.readWorkspaceBackground()
            # Style
            config['Look/currentStyle'] = self.config.readStyle()
            # Startup
            config['Startup/startupWorkingDirectory'] = self.config.readStartupWorkingDir()
            config['Startup/restoreLastSession'] = self.config.readRestoreLastSession()
            config['Geometry/position'] = self.config.readWindowPosition()
            config['Geometry/hsplitter'] = self.config.readHSplitterSizes()
            config['Geometry/vsplitter'] = self.config.readVSplitterSizes()
            config['Startup/lastWorkingDirectory'] = self.config.readLastWorkingDir()
            config['Recent/files'] = self.config.readRecentFiles()
            config['Session/files'] = self.config.readSessionFiles()
            config['HelpBrowser/history'] = self.config.readHelpBrowserHistory()
            config['HelpBrowser/bookmarks'] = self.config.readHelpBrowserBookmarks()

        return config


    def connectSignals(self):
        """
        Connect signals to slots.

        Signals coming from the menubar and toolbars are connected to
        slots of the application controller (VTApp).
        Signals coming from the tree view pane are connected to slots of
        the leaves manager.
        """

        # The mapping where actions are defined
        self.actions = self.gui.actions

        # Mapping between actions, the SIGNALs they can emit and the
        # slots the SIGNALs are connected to
        actionSignalSlot = {
            #
            # File menu
            #
            'fileNew':
            (self.actions['fileNew'],
            qt.SIGNAL('activated()'), self.slotFileNew),
            'fileOpen':
            (self.actions['fileOpen'],
            qt.SIGNAL('activated()'), self.slotFileOpen),
            'fileClose':
            (self.actions['fileClose'],
            qt.SIGNAL('activated()'), self.slotFileClose),
            'fileCloseAll':
            (self.actions['fileCloseAll'],
            qt.SIGNAL('activated()'), self.slotFileCloseAll),
            'fileSaveAs':
            (self.actions['fileSaveAs'],
            qt.SIGNAL('activated()'), self.slotFileSaveAs),
            'fileExit':
            (self.actions['fileExit'],
            qt.SIGNAL('activated()'), self.slotFileExit),
            'fileOpenRecent':
            (self.gui.openRecentSubmenu,
            qt.SIGNAL('aboutToShow()'), self.slotRecentSubmenuAboutToShow),
            #
            # Node menu
            #
            'nodeOpen':
            (self.actions['nodeOpen'],
            qt.SIGNAL('activated()'), self.slotNodeOpen),
            'nodeClose':
            (self.actions['nodeClose'],
            qt.SIGNAL('activated()'), self.slotNodeClose),
            'nodeProperties':
            (self.actions['nodeProperties'],
            qt.SIGNAL('activated()'), self.slotNodeProperties),
            'nodeNew':
            (self.actions['nodeNew'],
            qt.SIGNAL('activated()'), self.slotNodeNewGroup),
            'nodeRename':
            (self.actions['nodeRename'],
            qt.SIGNAL('activated()'), self.slotNodeRename),
            'nodeCut':
            (self.actions['nodeCut'],
            qt.SIGNAL('activated()'), self.slotNodeCut),
            'nodeCopy':
            (self.actions['nodeCopy'],
            qt.SIGNAL('activated()'), self.slotNodeCopy),
            'nodePaste':
            (self.actions['nodePaste'],
            qt.SIGNAL('activated()'), self.slotNodePaste),
            'nodeDelete':
            (self.actions['nodeDelete'],
            qt.SIGNAL('activated()'), self.slotNodeDelete),
            #
            # Query menu
            #
            'queryNew':
            (self.actions['queryNew'],
            qt.SIGNAL('activated()'), self.slotQueryNew),
##            'queryList':
##            (self.actions['queryList'],
##            SIGNAL('activated()'), self.slotQueryList),
#            'queryDelete':
#            (self.actions['queryDelete'],
#            SIGNAL('activated()'), self.slotQueryDelete),
            'queryDeleteAll':
            (self.actions['queryDeleteAll'],
            qt.SIGNAL('activated()'), self.slotQueryDeleteAll),
            #
            # Leaf menu
            #
            #
            # Window menu
            #
            'windowCascade':
            (self.actions['windowCascade'],
            qt.SIGNAL('activated()'), self.gui.workspace.cascade),
            'windowTile':
            (self.actions['windowTile'],
            qt.SIGNAL('activated()'), self.gui.workspace.tile),
            'windowClose':
            (self.actions['windowClose'],
            qt.SIGNAL('activated()'), self.slotWindowsClose),
            'windowCloseAll':
            (self.actions['windowCloseAll'],
            qt.SIGNAL('activated()'), self.slotWindowsCloseAll),
            'windowAbout':
            (self.gui.windowsMenu,
            qt.SIGNAL('aboutToShow()'), self.slotWindowsMenuAboutToShow),
            #
            # Tools menu
            #
            'toolsHideFileToolbar':
            (self.actions['toolsHideFileToolbar'],
            qt.SIGNAL('activated()'), self.slotToolsHideToolBar),
            'toolsHideLineUp':
            (self.actions['toolsHideLineUp'],
            qt.SIGNAL('activated()'), self.slotToolsLineUp),
            'toolsHideNodeToolbar':
            (self.actions['toolsHideNodeToolbar'],
            qt.SIGNAL('activated()'), self.slotToolsHideToolBar),
            'toolsHideHelpToolbar':
            (self.actions['toolsHideHelpToolbar'],
            qt.SIGNAL('activated()'), self.slotToolsHideToolBar),
            'toolsUserOptions':
            (self.actions['toolsUserOptions'],
            qt.SIGNAL('activated()'), self.slotToolsPreferences),
            #
            # Help menu
            #
            'helpAbout':
            (self.actions['helpAbout'],
            qt.SIGNAL('activated()'), self.slotHelpAbout),
            'helpUsersGuide':
            (self.actions['helpUsersGuide'],
            qt.SIGNAL('activated()'), self.slotHelpDocBrowser),
            'helpAboutQt':
            (self.actions['helpAboutQt'],
            qt.SIGNAL('activated()'), self.slotHelpAboutQt),
            'helpVersions':
            (self.actions['helpVersions'],
            qt.SIGNAL('activated()'), self.slotHelpVersions),
            'helpWhatsThis':
            (self.actions['helpWhatsThis'],
            qt.SIGNAL('activated()'), self.gui, qt.SLOT('whatsThis()'))
        }

        # Connect menubar actions and toolbars actions signals to slots
        for args in actionSignalSlot.values():
            apply(self.connect, args)

        # Connect tree view pane signals to slots
        self.connect(self.otLV, qt.PYSIGNAL('itemRenamedInplace(bool)'),
            self.slotNodeRename)

        self.connect(self.otLV, qt.SIGNAL("doubleClicked(QListViewItem *)"),
            self.slotNodeOpen)

        self.connect(self.otLV,
            qt.SIGNAL("contextMenuRequested(QListViewItem *, const QPoint &, int)"),
            self.slotContextualNodeMenu)

        self.connect(self.otLV, qt.SIGNAL("selectionChanged()"),
            self.slotUpdateSBNodeInfo)

        #
        # Synchronization between the tree view and the workspace
        #
        self.connect(self.workspace, qt.SIGNAL('windowActivated(QWidget *)'),
            self.slotSynchronizeTreeView)
        self.connect(self.otLV, qt.SIGNAL("selectionChanged()"),
            self.synchronizeWorkspace)

        #
        # QActions update
        #
        # When a window is activated or closed the Open View and Close
        # View actions need to be updated
        self.connect(self.workspace, qt.SIGNAL('windowActivated(QWidget *)'),
            self.slotUpdateActions)
        # When the item selected in the tree view changes most actions
        # may require un update
        self.connect(self.otLV, qt.SIGNAL("selectionChanged()"),
            self.slotUpdateActions)


    def slotUpdateSBNodeInfo(self):
        """Update the status bar text box showing the selected item path."""

        info = ''
        selected = self.otLV.selectedItem()
        if selected:
            info = selected.where
        self.gui.sbNodeInfo.setText(self.__tr('Selected node: %0.50s ',
            'A status bar message') %  info)


    def slotUpdateActions(self, window=None):
        """
        Update the state of the actions tied to menu items and toolbars.

        Every time that the selected item changes in the tree viewer the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.). The
        slot should be manually called when a new view is activated in the
        workspace (for instance by methods slotNodeOpen, slotNodeClose).

        .. _Warning:
        
        Warning! Don\'t call this method until the GUI initialisation finishes.
        It will fail if it is invoqued before the required database is open.
        This is the reason why connectSignals() is called as late as possible
        in the constructor.

        :Parameter window: an ``hpTable.HPTable`` instance
        """

        selected = self.otLV.selectedItem()
        if selected:
            top = selected.dbview.root_item
        else:
            top = None
        self.updateFileActions(selected, top)
        self.updateNodeActions(selected, top)
        # If the temporary DB is closed then DO NOT update query actions
        # It should happen only when we quit the application
        if self.queryRoot:
            self.updateQueryActions(selected, top)


    def synchronizeWorkspace(self):
        """
        Synchronize the tree view pane and the workspace.

        The driven force is state of the tree view pane. If the selected node
        has a view that view is raised. If it has no view then the active view
        is deactivated.
        
        Beware that the only way to deactivate the workspace active window
        is to activate a different one. The QEvent.WindowDeactivate and
        QEvent.WindowActivate events just change the look of the receiver
        window.
        """

        try:
            selected = self.otLV.selectedItem()
            key = "%s#@#%s" % (selected.getFilepath(), selected.where)
            selected_view = self.leavesManager._openLeaf[key][1].hp_table
        except (AttributeError, KeyError):
            selected_view = None
            active_view = self.workspace.activeWindow()

        if not selected_view:  # The selected node (if any) has no view
            wd_event = qt.QEvent(qt.QEvent.WindowDeactivate)
            # Don't send the event if there are no views in the workspace
            active_view and qt.qApp.sendEvent(active_view, wd_event)
        elif selected_view == self.workspace.activeWindow():
            wa_event = qt.QEvent(qt.QEvent.WindowActivate)
            qt.qApp.sendEvent(selected_view, wa_event)
        else:
            selected_view.setFocus()
        self.otLV.setFocus()


    def updateFileActions(self, selected=None, top=None):
        """
        Update the state of the actions tied to File menu/toolbar.

        Every time that the selected item changes in the tree viewer the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.).
        """

        # New, Open and Exit actions are allways enabled
        if self.dbManager.dbList():
            # Enable Close All menu item
            self.gui.actions['fileCloseAll'].setEnabled(1)
            if selected and top != self.queryRoot:
                # Enable Close and Save As menu item
                self.gui.actions['fileClose'].setEnabled(1)
                self.gui.actions['fileSaveAs'].setEnabled(1)
            else:
                # Disable Close and Save As menu item
                self.gui.actions['fileClose'].setEnabled(0)
                self.gui.actions['fileSaveAs'].setEnabled(0)
        else:
            # Disable Close, Close All and Save As menu item
            self.gui.actions['fileCloseAll'].setEnabled(0)
            self.gui.actions['fileClose'].setEnabled(0)
            self.gui.actions['fileSaveAs'].setEnabled(0)


    def updateNodeActions(self, selected=None, top=None):
        """
        Update the state of the actions tied to Node menu/toolbar.

        Every time that the selected item changes in the tree viewer or
        a view is opened/closed in the workspace the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.).

        Note: see `Warning`_ in the slotUpdateActions method.
        """

        # If there is not selected node all menu items are disabled
        if not selected:
            for ID in ['nodeOpen', 'nodeClose', 'nodeProperties', 'nodeNew',
                'nodeRename', 'nodeCut',  'nodeCopy', 'nodePaste', 'nodeDelete']:
                self.gui.actions[ID].setEnabled(0)
        else:
            filePath = selected.getFilepath()
            dbdoc = self.dbManager.getDB(filePath)
            mode = dbdoc.mode
            node = dbdoc.getNode(selected.where)
            node_is_group = hasattr(node, '_v_children')
            key = '%s#@#%s' % (filePath, selected.where)
            viewsList = self.leavesManager.viewList()

            # Any selected node can be copied and inspected
            self.gui.actions['nodeProperties'].setEnabled(1)
            self.gui.actions['nodeCopy'].setEnabled(1)

            # If the selected node is a group disable opening menu items
            if node_is_group:
                self.gui.actions['nodeOpen'].setEnabled(0)
                self.gui.actions['nodeClose'].setEnabled(0)
            else:
                # Setup open/close menu items depending on the currently
                # opened views
                if key in viewsList:
                    self.gui.actions['nodeOpen'].setEnabled(0)
                    self.gui.actions['nodeClose'].setEnabled(1)
                else:
                    self.gui.actions['nodeOpen'].setEnabled(1)
                    self.gui.actions['nodeClose'].setEnabled(0)

            # If the selected node is writable enable editing menu items
            if mode == 'r':
                # Node editing is disabled
                for ID in ['nodeNew', 'nodeRename', 'nodeCut',  'nodePaste',
                    'nodeDelete']:
                    self.gui.actions[ID].setEnabled(0)
            else:
                # Enabling/disabling actions depends on the kind of node
                # Root nodes cannot be renamed, cut or deleted
                for ID in ['nodeRename', 'nodeCut', 'nodeDelete']:
                    if selected == top:
                        self.gui.actions[ID].setEnabled(0)
                    else:
                        self.gui.actions[ID].setEnabled(1)
                # New nodes can be located under Group nodes...
                if node_is_group:
                    self.gui.actions['nodeNew'].setEnabled(1)
                    self.gui.actions['nodePaste'].setEnabled(1)
                # but not under Leaf nodes
                else:
                    self.gui.actions['nodeNew'].setEnabled(0)
                    self.gui.actions['nodePaste'].setEnabled(0)

            # Editing the Query results node is forbidden.
            if selected == self.queryRoot:
                self.gui.actions['nodeNew'].setEnabled(0)
                self.gui.actions['nodeCut'].setEnabled(0)
                self.gui.actions['nodePaste'].setEnabled(0)
                self.gui.actions['nodeRename'].setEnabled(0)
                self.gui.actions['nodeDelete'].setEnabled(0)


    def updateQueryActions(self, selected=None, top=None):
        """
        Update the state of the actions tied to Query menu/toolbar.

        Every time that the selected item changes in the tree viewer or
        a view is opened/closed in the workspace the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.).

        Note: see `Warning`_ in the slotUpdateActions method.
        """

        # Update the Query menu actions unless the temporary database
        # doesn't exist (i.e. the application is about to exit).
        if self.dbManager.tmp_dbdoc:
            qrootNode = self.dbManager.tmp_dbdoc.getNode(self.queryRoot.where)
            if qrootNode._v_nchildren:
                self.gui.actions['queryDeleteAll'].setEnabled(1)
            else:
                self.gui.actions['queryDeleteAll'].setEnabled(0)
        else:
            return

        self.gui.actions['queryNew'].setEnabled(0)
        if selected:
            filePath = selected.getFilepath()
            dbdoc = self.dbManager.getDB(filePath)
            node = dbdoc.getNode(selected.where)
            if hasattr(node, 'description'):
                self.gui.actions['queryNew'].setEnabled(1)


    def initSettings(self, current_config):
        """
        Set the initial configuration of the application.

        Note for Unix users: ``QSettings`` stores configuration settings
        in a (plain text) config file so we must beware of ``QSettings``
        search algorithms and name conventions in order to find that
        file. When a ``QSettings`` read method is invoqued, it traverses
        the following directories searching for the config file

        - $QTDIR/etc/settings
        - $HOME/.vitables
        - $HOME/.qt

        and reads from the **last** config file found on which it has
        reading permissions. So, if we want to use $HOME/.vitables
        we must be sure that there is not a readable config file in
        $HOME/.qt
        """

        # Current configuration is applied in two steps, first the
        # preferences,  then the rest of settings
        self.applyPreferences(current_config)
        [x, y, width, height] = current_config['Geometry/position']
        self.gui.move(qt.QPoint(x ,y))
        self.gui.resize(qt.QSize(width, height))
        self.gui.hsplitter.setSizes(current_config['Geometry/hsplitter'])
        self.gui.vsplitter.setSizes(current_config['Geometry/vsplitter'])
        self.lastWorkingDirectory = \
            current_config['Startup/lastWorkingDirectory']
        self.recentFilesList = current_config['Recent/files']
        self.sessionFilesNodes = current_config['Session/files']
        self.hbHistory = current_config['HelpBrowser/history']
        self.hbBookmarks = current_config['HelpBrowser/bookmarks']

        # If the configuration is not saved on disk (as it happens
        # when the package is just installed) then save it.
        base_key = self.config.base_key
        lookEntry = self.config.entryList('%s/Look' % base_key)
        if not lookEntry:
            self.saveConfiguration()
            print self.__tr('ViTables configuration saved!',
                'Application configuration succesfully saved')


    def updateRecentFiles(self, filePath, mode):
        """
        Add a new path to the list of most recently open files.

        ``processCommandLineArgs``, ``recoverLastSession``, ``slotFileNew``,
        and ``slotFileOpen`` call this method.

        :Parameters:
        
            - `filePath`: the last opened/created file
            - `mode`: the opening mode of the file
        """

        if isinstance(filePath, qt.QString):
            filePath = filePath.latin1()
        item = '%s#@#%s' % (mode, vitables.utils.forwardPath(filePath))

        # Updates the list of recently open files. Most recent goes first.
        if not item in self.recentFilesList:
            self.recentFilesList.insert(0, item)
            if len(self.recentFilesList) > self.numberOfRecentFiles:
               self.recentFilesList.pop()
        else:
            self.recentFilesList.remove(item)
            self.recentFilesList.insert(0, item)


    def recoverLastSession(self):
        """
        Recover the last open session.

        This method will attempt to open those files and leaf views that
        were opened the last time the user closed ViTables.
        The lists of files and leaves is read from the configuration.
        The format is::

            ['filepath1#@#mode#@#nodepath1#@#nodepath2, ...',
            'filepath2#@#mode#@#nodepath1#@#nodepath2, ...', ...]

        Eventually, the history list is updated.
        """

        print self.__tr('Recovering last session...', 'A logger message')
        for file_data in self.sessionFilesNodes:
            item = file_data.split('#@#')
            # item looks like [filepath1, mode, nodepath1, nodepath2, ...]
            filePath = item.pop(0)
            filePath = vitables.utils.forwardPath(filePath)
            mode = item.pop(0)
            # Open the database --> add the tree view to the tree pane.
            # The view contains only the root node
            if self.dbManager.openDB(filePath, mode):
                dbTree = self.dbManager.getDBView(filePath)
                rootItem = dbTree.getRootItem()
                # Update the history file
                self.updateRecentFiles(filePath, mode)

                # After popping item looks like [nodepath1, nodepath2, ...]
                for nodePath in item:
                    # We have to add the wanted leaf to the tree view in a explicit way
                    if dbTree.addNode(nodePath):
                        # After adding the node we expand the dbview and show the added leaf
                        for leafItem in treeView.deepLVIterator(rootItem):
                            if nodePath == leafItem.where:
                                self.slotNodeOpen(leafItem)
                                break
        print self.__tr('Recovering finished.', 'A logger message')


    #
    # slot functions that handle user input: File menu ########################
    #


    def processCommandLineArgs(self, mode='', h5files=[], dblist=''):
        """Open files passed in the command line."""

        # The database manager opens the files (if any)
        for filePath in h5files:
            filePath = vitables.utils.forwardPath(filePath)
            if self.dbManager.openDB(filePath, mode):
                db = self.dbManager.getDB(filePath)
                if db:
                        self.updateRecentFiles(filePath, mode)

        # If a list of files is passed then parse the list and open the files
        if dblist:
            print 'Loading list of files from %s...' % dblist
            try:
                input = open(dblist, 'r')
                lines = [line[:-1].split('#@#') for line in input.readlines()]
                input.close()
                for l in lines:
                    if len(l) !=2:
                        print self.__tr('Skipping line %s' % l, 'Bad line format')
                        continue
                    mode, filePath = l
                    filePath = vitables.utils.forwardPath(filePath)
                    if not mode in ['r', 'a']:
                        print self.__tr('Skipping line %s' % l, 'Bad line format')
                        continue
                    if self.dbManager.openDB(filePath, mode):
                        db = self.dbManager.getDB(filePath)
                        if db:
                                self.updateRecentFiles(filePath, mode)
            except IOError:
                print self.__tr("""\nError: list of HDF5 files not read""",
                    'File not updated error')


    def openFileDlg(self, name, mode, caption, new_file=False):
        """
        Open a file dialog adequate for create/save/open hdf5 files.

        This method is reused by slotFileOpen, slotFileSaveAs and
        slotFileNew methods.

        :Parameters:

            - `name`: the dialog name
            - `mode`: indicate what the user may select in the file dialog
            - `caption`: the dialog caption
            - `new_file`: true if a new file is being created

        :Returns: the full path of the selected file
        """

        # Create the dialog
        fileDlg = qt.QFileDialog(self.gui, name, 1)
        fileDlg.setFilters(self.__tr("""HDF5 Files (*.h5 *.hd5 *.hdf5);;"""
            """All Files (*)""",
            'File filter for the Open File dialog'))

        # Customize the dialog icons, caption and mode
        fileDlg.setCaption(caption)
        fileDlg.setMode(mode)

        # Add a Read-only widget to the bottom of the dialog
        if not new_file:
            read_onlyL = qt.QLabel(self.__tr('Read-only:',
                'Label in the file manager dialog'), fileDlg)
            read_onlyW = qt.QWidget(fileDlg)
            read_onlyWL = qt.QHBoxLayout(read_onlyW, 5)
            read_onlyCB = qt.QCheckBox(read_onlyW)
            read_onlyWL.addWidget(read_onlyCB)
            read_onlyWL.addStretch(1)
            fileDlg.addWidgets(read_onlyL, read_onlyW, None)
            if vtconfig.getVersion().endswith('eval'):
                read_onlyCB.setChecked(True)
                read_onlyCB.setEnabled(False)

        # The working directory is the last directory opened in
        # the current session except for the very first time than
        # the dialog is raised
        if self.isStartup:
            self.isStartup = False
            if self.startupWorkingDirectory == 'home':
                self.lastWorkingDirectory = 'home'

        # The lastWorkingDirectory attribute says to the QFileDialog
        # widget where to start
        if self.lastWorkingDirectory == 'home':
            self.lastWorkingDirectory = vitables.utils.getHomeDir()
        fileDlg.setDir(qt.QDir(self.lastWorkingDirectory))

        # Execute the dialog
        try:
            fileDlg.exec_loop()
            # OK clicked. Working directory is updated
            if fileDlg.result() == qt.QDialog.Accepted:
                # The absolut path of the selected file
                filePath = fileDlg.selectedFile()
                # Update the working directory
                self.lastWorkingDirectory = fileDlg.dir().canonicalPath().latin1()
                # The file opening mode depends on the checkbox state
                if not new_file:
                    if read_onlyCB.isChecked():
                        mode = 'r'
                    else:
                        mode = 'a'
            # Cancel clicked. Working directory doesn't change
            else:
                filePath = qt.QString('')
        finally:
            del fileDlg

        # Return the result
        if not new_file:
            return filePath, mode
        else:
            return filePath


    def checkFileExtension(self, filePath):
        """
        Check the filename extension of a given file.

        If the filename has no extension this method adds .h5
        extension to it. This is useful when a file is being created or
        saved.

        :Parameter filePath: the full path of the file (a QString)

        :Returns: the filepath with the proper extension (a Python string)
        """

        filePath = filePath.latin1()
        if not re.search('\.(.+)$', os.path.basename(filePath)):
            ext = '.h5'
            filePath = '%s%s' % (filePath, ext)
        return filePath


    def slotFileNew(self):
        """Create a new file."""

        # Get the file path
        filePath = self.openFileDlg('create file dialog',
            qt.QFileDialog.AnyFile,
            self.__tr('Creating a new file...',
                'Caption of the File creation dialog'), 1)
        if filePath.isEmpty():
            # Abort if the user cancels the dialog
            return
        # Check the file extension
        filePath = self.checkFileExtension(filePath)

        # Check the returned path
        filePath = os.path.abspath(filePath)
        if os.path.exists(filePath):
            print self.__tr(
                """The selected file already exists. Please try it again.""",
                'A file creation error')
            return

        # Create the pytables file and close it.
        # creationOK will be True if the file is succesfully created
        # and False if not.
        creation_ok = self.dbManager.createFile(filePath)
        if not creation_ok:
            print self.__tr(
                """\nFile creation failed due to unknown reasons!\nPlease, """
                """have a look to the last error displayed in the """
                """logger. If you think it's a bug, please report it"""
                """ to developers.""",
                'A file creation error')
        else:
            # The write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            self.updateRecentFiles(filePath, 'a')


    def slotFileSaveAs(self):
        """
        Save a renamed copy of a file.

        This method exhibits the typical behavior: copied file is closed
        and the fresh renamed copy is open.
        """

        current = self.otLV.selectedItem()
        current_filepath = current.getFilepath()
        initial_filename = os.path.basename(current_filepath)

        # Get the destination name
        candidate = \
            self.openFileDlg('save as... file dialog',
            qt.QFileDialog.AnyFile,
            self.__tr('Saving a file copy...',
                'Caption of the File Save As... dialog'), 1)
        if candidate.isEmpty():
            # Abort if the user cancels the dialog
            return
        elif candidate.latin1() == current_filepath:
            return

        # Check the file extension
        candidate = self.checkFileExtension(candidate)

        # Check if the chosen name is already in use
        dirname, filename = os.path.split(candidate)
        src_data = [initial_filename, self.dbManager.tmp_filepath]
        target_data = [dirname, filename]
        final_filename, overwrite = dbManager.getFinalName('save_as', target_data,
            src_data)
        if not final_filename:
            return

        final_filepath = tables.path.joinPath(dirname, final_filename)

        # If an open file is overwritten then close it
        if overwrite and self.dbManager.getDB(final_filepath):
            top = treeView.findTreeItem(self.otLV, final_filepath, '/')
            self.slotFileClose(top)

        # Make a copy of the selected file
        self.dbManager.copyFile(current_filepath, final_filepath)

        # Close the copied file and open the new copy in read-write mode
        src_top = current.dbview.root_item
        # Substitute the saved file by the new file.
        # The root group of the just opened file is the selected item
        self.slotFileOpen(qt.QString(final_filepath), 'a')
        dst_top = self.otLV.selectedItem()
        dst_top.moveItem(src_top)
        self.slotFileClose(src_top)


    def slotFileOpen(self, filePath=None, mode='a'):
        """
        Open a file that contains a ``PyTables`` database.

        When this method is invoqued with ``File --> Open`` then no filePath
        is passed and a dialog (with the read-only check box) is raised.
        When the method is invoqued via slotRecentSubmenuActivated or
        slotFileSaveAs methods then filePath is passed and the dialog
        is not raised.

        :Parameters:

            - `filePath`: the full path of the file to be opened
            - `mode`: the file opening mode. It can be read-write or read-only
        """

        if not filePath:
            # Gets a QString with the full path of the file we want to open.
            filePath, mode = \
                self.openFileDlg('open file dialog',
                qt.QFileDialog.ExistingFile,
                self.__tr('Select a file for opening',
                    'Caption of Open file dialog'))

        if not filePath:
            # The user has canceled the dialog
            return

        # Make sure the path is not a relative path
        filePath = os.path.abspath(filePath.latin1())

        filePath = vitables.utils.forwardPath(filePath)
        # The database manager opens the file. Beware that in corner cases
        # the opening mode may be different from the asked one
        opendb_ok = self.dbManager.openDB(filePath, mode)
        if opendb_ok:
            db = self.dbManager.getDB(filePath)
            if db:
                self.updateRecentFiles(filePath, db.getFileMode())


    def slotFileClose(self, current=None, update=True):
        """
        Close a file.

        First of all this method finds out which database it has to close.
        Afterwards all views belonging to that database are closed, then
        the object tree is removed from the QListView and, finally, the
        database is closed.

        current: a node living in the file being closed
        update: indicates if the update actions slot should be called or not
        """

        if not current:
            current = self.otLV.selectedItem()
        # Clear the status bar and get rid of potential problems that could
        # appear if we remove from the tree view an item when its path is
        # being displayed (by the leaves manager timer) in the status bar
        self.gui.statusBar().clear()

        # The top level item from which the selected node hungs
        top = current.dbview.root_item
        # Every existing leaf view is deleted from the workspace
        self.slotNodeClose(top)

        # The database manager closes the file and delete its root item
        # from the tree viewer
        filePath = current.getFilepath()
        self.dbManager.closeDB(filePath)
        # The emission of SIGNAL selectionChanged is forced. It ensures
        # that when this method is called repeatedly for non selected
        # items (as it can happen in VTApp.slotFileCloseAll) the
        # QActions will be properly updated
        self.otLV.emit(qt.SIGNAL('selectionChanged()'), ())


    def slotFileCloseAll(self,):
        """Close every file opened by user."""

        # The list of top level items to be removed.
        # The temporary database should be closed at quit time only
        root_list = [top for top in treeView.flatLVIterator(self.otLV)]
        root_list.remove(self.queryRoot)
        # The iterator cannot be used directly because removing the items
        # being iterated corrupts the iterator (as it would happen with a list)
        for root_item in root_list:
            self.slotFileClose(root_item)


    def slotFileExit(self):
        """
        Safely closes the application.

        Save current configuration on disk, closes opened files and exits.
        """

        # Close all browsers
        if len(self.docBrowsers) > 0:
            self.docBrowsers[0].slotExitBrowser()
        # Save current configuration
        self.saveConfiguration()
        # Close every user opened file
        self.slotFileCloseAll()
        # Close the temporary database
        self.slotFileClose(self.queryRoot, update=False)
        self.queryRoot = None
        # Application quit
        qt.qApp.quit()


    def slotRecentSubmenuAboutToShow(self):
        """Update the content of the Open Recent File submenu."""

        self.gui.openRecentSubmenu.clear()
        at = 0
        iconset = vitables.utils.getIcons()
        for item in self.recentFilesList:
            at += 1
            (mode, filePath) = item.split('#@#')
            if mode == 'r':
                self.gui.openRecentSubmenu.insertItem(iconset['file_ro'],
                    '%s. %s' % (at, filePath), self.openRecentFile)
            else:
                self.gui.openRecentSubmenu.insertItem(iconset['file_rw'],
                    '%s. %s' % (at, filePath), self.openRecentFile)
        if self.recentFilesList:
            self.gui.openRecentSubmenu.insertSeparator()
            self.gui.openRecentSubmenu.insertItem(self.__tr('&Clear',
                'A recent submenu command'),
                self.clearRecentFiles)


    def openRecentFile(self, itemID):
        """
        Opens the file whose path appears in the activated menu item text.

        :Parameter `itemID`: 
            the activated menu item ID in the ``Open Recent File`` submenu.
        """

        iconset = vitables.utils.getIcons()
        menu = self.gui.openRecentSubmenu
        # Menu items text looks like: index. filePath
        itemText = menu.text(itemID)
        pixmapID = menu.iconSet(itemID).pixmap().serialNumber()
        regexp = qt.QRegExp('\d+\. (.*)')
        regexp.search(itemText)
        filePath = regexp.cap(1)
        if pixmapID == iconset['file_ro'].pixmap().serialNumber():
            self.slotFileOpen(filePath, mode='r')
        elif pixmapID == iconset['file_rw'].pixmap().serialNumber():
            self.slotFileOpen(filePath)


    def clearRecentFiles(self):
        """
        Clear the list of recently opened files and delete the corresponding
        historical file.
        """

        self.recentFilesList = []


    #
    # slot functions that handle user input: Node menu ########################
    #


    def slotNodeOpen(self, current=None):
        """
        Opens a node for viewing.

        This method can be called by activating ``Node --> Open`` (what passes
        no argument) or, by doing a double click on a tree view item (what
        emits a SIGNAL that passes an argument to its connected slot).
        If the target node is a group it is expanded/collapsed by default. If
        not, the node content is displayed by the leaves manager.

        :Parameter current: the tree view item to be open
        """

        # Node --> Open doesn't pass the current argument
        if not current:
            current = self.otLV.selectedItem()

        # Open the selected item if it is not a group
        if not current.isExpandable():
            doc = self.leavesManager.getLeafDoc(current)
            if doc:
                # The document already exists. Its view is raised
                view = self.leavesManager.getLeafView(doc.filepath, doc.nodepath)
                self.raiseView(view.hp_table)
            else:
                # The document has to be created
                dbdoc = self.dbManager.getDB(current.getFilepath())
                doc = self.leavesManager.createLeafDoc(dbdoc, current.where)
                if doc.isInstanceOf('UnImplemented'):
                    self.leavesManager.slotUnImplementedMsg()
                elif 0L in doc.getShape():
                    print self.__tr("""Caveat: dataset is empty. Nothing to show.""",
                        'Warning message for users')
                elif doc.isReadable():
                    # Tracks the document and ties it to a view
                    self.leavesManager.createViewAndTrack(doc, current)


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

        # Node --> Close doesn't pass the current argument
        if not current:
            current = self.otLV.selectedItem()

        dbdoc = self.dbManager.getDB(current.getFilepath())
        nodepath = current.where
        key = '%s#@#%s' % (dbdoc.filepath, nodepath)
        if nodepath == '/':
            self.leavesManager.cleanLeavesUnderKey(key)
        else:
            self.leavesManager.closeView(key)


    def slotNodeNewGroup(self):
        """Create a new group node."""

        selected = self.otLV.selectedItem()

        # Get a candidate name for the new group
        filepath = selected.getFilepath()
        where = selected.where
        header = self.__tr(
            """<qt>
            File path: %s<br>Parent group: %s
            </qt>""",
            'Text in the New Group dialog') % (filepath, where)
        candidate = dbManager.getInitialName(header, '',
            self.__tr('Group name: ', 'Label in the New group dialog'),
            self.__tr('New group', 'Caption in the New group dialog'))
        if not candidate:
            # Cancel button clicked
            return

        # Get the tables.File instance
        dbdoc = self.dbManager.getDB(filepath)

        # Check if the chosen name is already in use
        parent_group = dbdoc.getNode(where)
        target_data = [filepath, where, candidate, parent_group]
        final_name, overwrite = dbManager.getFinalName("create_group", target_data, [])
        if not final_name:
            # Cancel button clicked
            return

        # If the creation overwrites a group with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            node_key = '%s#@#%s' % (dbdoc.filepath, where)
            self.leavesManager.cleanLeavesUnderKey(node_key)

        self.dbManager.createGroup(filepath, where, final_name)


    def slotNodeCut(self):
        """Cut the selected node."""

        # Empty the clipboard and the hidden group where cut nodes live.
        # If a sequence of copy and cut operations is executed then only
        # the last cut/copied node will be considered by future paste
        # operations
        self.dbManager.clearHiddenGroup()
        qt.qApp.clipboard().setText('')

        selected = self.otLV.selectedItem()

        # The database where the node being copied lives
        dbdoc = self.dbManager.getDB(selected.getFilepath())

        # If the cut node has attached views then these views are closed
        # before the cutting is done. This behavior can be inconvenient
        # for users but get rid of potential problems that arise if, for
        # any reason, the user doesn't paste the cut node.
        node_key = '%s#@#%s' % (dbdoc.filepath, selected.where)
        where, nodename = os.path.split(selected.where)
        self.leavesManager.cleanLeavesUnderKey(node_key)

        # Cut the node
        self.dbManager.cut(dbdoc, where, nodename)


    def slotNodeCopy(self, selected=None):
        """
        Copy the selected node to the XWindow clipboard.

        A node is copied when it is dragged or when the copy action is
        launched from the Node menu. In both cases the copied node is
        the selected node.

        :Parameter selected: the tree view item to be copied
        """

        # Empty the clipboard and the hidden group where cut nodes live.
        # If a sequence of copy and cut operations is executed then only
        # the last cut/copied node will be considered by future paste
        # operations
        self.dbManager.clearHiddenGroup()
        qt.qApp.clipboard().setText('')

        if not selected:
        	selected = self.otLV.selectedItem()

        self.paste_disabled_item = None

        # The database where the node being copied lives
        dbdoc = self.dbManager.getDB(selected.getFilepath())

        # Non readable leaves will not be copied
        if not selected.isExpandable():
            # If the document to be read is closed then create it
            node_doc = self.leavesManager.getLeafDoc(selected) or \
                self.leavesManager.createLeafDoc(dbdoc, selected.where)
            if not node_doc.isReadable():
                return

        # Copy the node and ensure that the node won't be pasted on itself
        encoded_obj = self.otLV.encodeNode(dbdoc.filepath, selected.where)
        self.paste_disabled_item = selected

        return encoded_obj


    def slotNodePaste(self, target=None):
        """
        Paste the content of the XWindow clipboard under the selected node.

        If a node is moved (i.e. dragged) from a database opened in read-only
        mode then the destination node is passed to the target argument.

        :Parameter target:
            the destination tree view item of the read-only dragged item
        """

        if not target:
            target = self.otLV.selectedItem()

        # The destination database
        target_dbdoc = self.dbManager.getDB(target.getFilepath())

        cut_nodes = self.dbManager.getCutNodes()

        # Check if paste is allowed. For copied nodes it is forbidden when:
        # - source and target are the same node
        # - target is the source's parent
        if self.paste_disabled_item and (not cut_nodes):
            if target == self.paste_disabled_item:
                print self.__tr("""\nError: operation not allowed. """
                    """Source and destination are the same node.""",
                    'Paste node forbidden error')
                return

        # Get the name of the node being pasted
        if cut_nodes:
            nodename = os.path.basename(cut_nodes[0])
            src_nodepath = '%s/%s' % (self.dbManager.hidden_where, nodename)
            src_filepath = self.dbManager.tmp_filepath
            src_dbdoc = self.dbManager.tmp_dbdoc
        elif not qt.qApp.clipboard().text():
            return
        else:
            data = qt.QString()
            decode = qt.QTextDrag.decode(qt.qApp.clipboard().data(), data)
            if decode:
                data = data.latin1()
                src_filepath, src_nodepath = data.split('#@#')
                nodename = src_nodepath.split('/')[-1] or '/'
                src_dbdoc = self.dbManager.getDB(src_filepath)
                # If the node being pasted doesn't exist then do nothing
                if not src_nodepath in src_dbdoc.listNodes():
                    return

        # Check if in the destination group there is some node with the
        # same name than the node being pasted.
        target_nodepath = target.where
        parent_group = target_dbdoc.getNode(target_nodepath)
        target_data = [target.getFilepath(), target_nodepath, nodename, parent_group]
        src_data = [src_filepath, src_nodepath]
        final_name, overwrite = dbManager.getFinalName("paste_node", target_data,
            src_data)
        if not final_name:
            return

        # If the pasting overwrites a node with attached views then these
        # views are closed before the pasting is done
        if overwrite:
            nodepath = tables.path.joinPath(target_nodepath, final_name)
            node_key = '%s#@#%s' % (target_dbdoc.filepath, nodepath)
            self.leavesManager.cleanLeavesUnderKey(node_key)

        # Paste the copied/cut node
        self.dbManager.paste(src_dbdoc, src_nodepath, target_dbdoc,
            target_nodepath, final_name)


    def dropNode(self, source, target):
        """
        Move a node to a different location.

        This method handles dropped events coming from TreeNode instances.

        :Parameters:

            - `source`: the tree view item being dragged
            - `target`: the tree view item where source is being dropped
        """

        # The source and destination databases
        src_dbdoc = self.dbManager.getDB(source.getFilepath())
        target_dbdoc = self.dbManager.getDB(target.getFilepath())

        # The full paths of source and destination nodes
        src_nodepath = source.where
        target_nodepath = target.where

        # Check is paste is allowed. It is forbidden when:
        # - source and target are the same node
        # - target is the source's parent
        if target == source:
            print self.__tr("""\nError: operation not allowed. """
                """Source and destination are the same node.""",
                'Paste node forbidden error')
            return
        elif target == source.parent():
            # HDF51.6.5 has a bug that makes pytables to crash if
            # the node is overwritten in this situation.
            print self.__tr("""\nError: operation not allowed. """
                """A node cannot be added to its parent group.""",
                'Paste node forbidden error')
            return

        # Get the name of the node being pasted
        nodename = source.text(0).latin1()

        # Check if in the destination group there is some node with the
        # same name than the node being dropped.
        target_nodepath = target.where
        parent_group = target_dbdoc.getNode(target_nodepath)
        target_data = [target.getFilepath(), target_nodepath, nodename, parent_group]
        src_data = [source.getFilepath(), src_nodepath]
        final_name, overwrite = dbManager.getFinalName("move_node", target_data,
            src_data)
        if not final_name:
            return

        # If the dropping overwrites a node with attached views then these
        # views are closed before the dropping is done
        if overwrite:
            final_nodepath = tables.path.joinPath(target_nodepath, final_name)
            node_key = '%s#@#%s' % (target_dbdoc.filepath, final_nodepath)
            self.leavesManager.cleanLeavesUnderKey(node_key)

        # Drop the node
        self.dbManager.dropNode(src_dbdoc, src_nodepath, target_dbdoc,
            target_nodepath, final_name)

        # Update the views tied to the moved node and its descendants
        final_nodepath = tables.path.joinPath(target_nodepath, final_name)
        self.leavesManager.move(src_nodepath, final_nodepath,
            src_dbdoc.filepath, target_dbdoc)


    def slotNodeRename(self, inplace=False):
        """
        Rename the selected node.

        - ask for the node name
        - check the node name. If it is already in use ask what to<br>
          do (possibilities are rename, overwrite and cancel creation)
        - rename the node

        :Parameter inplace:
            indicates if the item is being renamed inplace or not
        """

        selected = self.otLV.selectedItem()

        # The database where the node being renamed lives
        filepath = selected.getFilepath()
        dbdoc = self.dbManager.getDB(filepath)
        (parent_path, initial_name) = os.path.split(selected.where)

        # The new nodename can be entered in two different ways
        # 1) inplace. It has already been entered (see TreeNode class)
        # but needs checking.
        # 2) via dialog. It still hasn't been entered.
        if inplace:
            candidate = selected.text(0).latin1()
        else:
            header = self.__tr(
                """<qt>
                File path: %s<br>Node path: %s
                </qt>""",
               'Text in the Node Rename dialog') % (filepath, selected.where)
            candidate = dbManager.getInitialName(header, initial_name,
                self.__tr('New name: ', 'Label in the Node renaming dialog'),
                self.__tr('Node renaming', 'Dialog caption'))

        # In trivial cases do nothing
        if not candidate:
            selected.setText(0, initial_name)
            return
        if candidate == initial_name:
            return

        # Check if the chosen name is already in use
        parent_group = dbdoc.getNode(parent_path)
        target_data = [filepath, parent_path, candidate, parent_group]
        src_data = [initial_name]
        final_name, overwrite = dbManager.getFinalName("rename_node", 
            target_data, src_data)
        # If Cancel button is clicked or the initial name is returned
        if (not final_name) or (final_name == initial_name):
            selected.setText(0, initial_name)
            return

        # If the renaming overwrites a node with attached views then these
        # views are closed before the renaming is done
        if overwrite:
            nodepath = tables.path.joinPath(parent_path, final_name)
            node_key = '%s#@#%s' % (dbdoc.filepath, nodepath)
            self.leavesManager.cleanLeavesUnderKey(node_key)

        # Rename the node
        initial_path = selected.where
        self.dbManager.rename(dbdoc, parent_path, final_name, initial_name)
        final_path = selected.where

        # Update views related to the renamed node
        self.leavesManager.rename(dbdoc.filepath, final_path, initial_path)

        # Update the Selected node indicator of the status bar
        self.slotUpdateSBNodeInfo()


    def slotNodeDelete(self, lvitem=None, force=None):
        """
        Delete a given node.

        :Parameters;

            - `lvitem`: the item being deleted from the tree view
            - `force`: ask/do not ask for confirmation before deletion
        """

        if not lvitem:
            lvitem = self.otLV.selectedItem()

        # Confirm deletion dialog
        if not force:
            del_dlg = qt.QMessageBox.question(self.gui,
                self.__tr('Node deletion',
                'Caption of the node deletion dialog'),
                self.__tr("""\nYou are about to delete the node:\n%s\n""",
                'Ask for confirmation') % lvitem.where,
                qt.QMessageBox.Ok|qt.QMessageBox.Default,
                qt.QMessageBox.Cancel|qt.QMessageBox.Escape,
                qt.QMessageBox.NoButton)

            # OK returns Accept, Cancel returns Reject
            if del_dlg == qt.QMessageBox.Cancel:
                return

        # The database where the node being renamed lives
        dbdoc = self.dbManager.getDB(lvitem.getFilepath())

        file_path = dbdoc.filepath
        (where, name) = os.path.split(lvitem.where)

        # If item is a filtered table then update the list of used names
#        if item.parent() == self.queryRoot:
#            self.ftnames.remove(item.text(0).latin1())

        # If the deletion involves a node with attached views then these
        # views are closed before the deletion is done
        node_key = '%s#@#%s' % (dbdoc.filepath, lvitem.where)
        self.leavesManager.cleanLeavesUnderKey(node_key)

        # Delete the node
        self.dbManager.delete(dbdoc, where, name)

        # The emission of SIGNAL selectionChanged is forced. It ensures
        # that when this method is called repeatedly for non selected
        # items (as it can happen in VTApp.slotQueryDeleteAll) the
        # QActions will be properly updated
        self.otLV.emit(qt.SIGNAL('selectionChanged()'), ())


    def slotNodeProperties(self):
        """
        Display the properties dialog for the currently selected node.

        The method is called by activating Node --> Properties.
        """

        current = self.otLV.selectedItem()
        dbdoc = self.dbManager.getDB(current.getFilepath())
        self.leavesManager.slotNodeProperties(dbdoc, current)


    def slotContextualNodeMenu(self, item, point, column):
        """
        The node contextual menu.

        When an item of the tree view is right clicked, a contextual
        popup is displayed. The content of the popup is the same than
        the content of the Node menu.

        :Parameters:

            - `item`: the QListViewItem right clicked, if any
            - `point`: the clicked point in global coordinates
            - `column`: the clicked column, if any
        """

        if not item:
            # Contextual menu for the tree pane
            self.gui.fileMenu.popup(point)
            return

        dbdoc = self.dbManager.getDB(item.getFilepath())
        node = dbdoc.getNode(item.where)
        # Contextual menu for root nodes
        if item.where == '/':
            self.gui.rootNodeCM.popup(point)
        # Contextual menu for Group nodes
        elif hasattr(node, '_v_nchildren'):
            self.gui.groupNodeCM.popup(point)
        # Contextual menu for Leaf nodes
        else:
            self.gui.leafNodeCM.popup(point)


    #
    # slot functions that handle user input: Query menu #####################
    #


    def slotQueryNew(self):
        """
        Add a new filtered table item to the query results tree.

        The creation process has 2 steps:

        - create the filtered table in the temporary database
        - add the filtered table to the Query results tree in the tree pane

        Finally the filtered table is opened.
        """

        selected = self.otLV.selectedItem()
        dbdoc = self.dbManager.getDB(selected.getFilepath())
        leafdoc = self.leavesManager.getLeafDoc(selected) or \
            self.leavesManager.createLeafDoc(dbdoc, selected.where)

        # The updateQueryActions method ensures that leafdoc is tied to
        # a tables.Table instance so we can query it with no more checking
        tmp_h5file = self.dbManager.tmp_dbdoc.getH5File()
        ftName, frows = self.leavesManager.queryTable(leafdoc, tmp_h5file)

        if ftName:
            # Update temporary database view
            tmp_dbview = self.dbManager.tmp_dbdoc.dbview
            tmp_dbview.addNode('/%s' % ftName)
            # Open the filtered table
            self.queryRoot.setOpen(1)
            for ftable in treeView.flatLVIterator(self.queryRoot):
                if ftable.text(0).latin1() == ftName:
                    break
            if frows:
                self.slotNodeOpen(ftable)
            else:
                print self.__tr("""Query result: no rows fulfill the """
                    """supplied condition, the table %s is empty.""",
                    'Empty filtered table notification') % ftName


    def slotQueryList(self):
        """
        """
        pass


    def slotQueryDeleteAll(self):
        """Delete all nodes from the query results tree."""

        delQBox = qt.QMessageBox.question(self.gui,
            self.__tr('Deleting all queries',
            'Caption of the QueryDeleteAll dialog'),
            self.__tr("""\n\nYou are about to delete all nodes """
                """under Query results\n\n""", 'Ask for confirmation'),
            qt.QMessageBox.Ok|qt.QMessageBox.Default,
            qt.QMessageBox.Cancel|qt.QMessageBox.Escape,
            qt.QMessageBox.NoButton)

        # OK returns Accept, Cancel returns Reject
        if delQBox == qt.QMessageBox.Cancel:
            return

        nodes = \
            [item for item in treeView.flatLVIterator(self.queryRoot)]
        for item in nodes:
            self.slotNodeDelete(item, force=True)
        # Reset the counter of filtered tables and the list of used names
        self.leavesManager.counter = 0
        self.leavesManager.ft_names = []
        self.leavesManager.last_query_info = ['', '', '']


    #
    # slot functions that handle user input: Windows menu #####################
    #


    def slotWindowsMenuAboutToShow(self):
        """
        Update the Windows menu.

        The Windows menu is dynamic because its content is determined
        by the currently open views. Because the number of these views or
        its contents may vary at any moment we must update the Windows
        menu every time it is open. For simplicity we don't keep track
        of changes in the menu content. Instead, we clean and create it
        from scratch every time it is about to show.
        """

        lastItemPosition = self.gui.windowsMenu.count() - 1
        # Clean the menu items corresponding to open views. These items tell
        # us which views were open last time the menu was popped. They don't
        # necessarely correspond to the currently open views.
        while lastItemPosition > self.gui.lastCoreItemPosition:
            self.gui.windowsMenu.removeItemAt(lastItemPosition)
            lastItemPosition-=1

        # And inserts the items corresponding to the views currently open.
        windowsList = self.workspace.windowList(qt.QWorkspace.CreationOrder)
        i = 0
        self.menuToWindowMap = {}
        for window in windowsList:
            i+=1
            index = self.gui.windowsMenu.insertItem(('&%i ' % i) +
                window.caption().latin1(), self.activateWindow)
            self.menuToWindowMap[index] = window
            if self.workspace.activeWindow() == window:
                self.gui.windowsMenu.setItemChecked(index, 1)

        if not windowsList:
            self.actions['windowsActionGroup'].setEnabled(0)
        else:
            self.actions['windowsActionGroup'].setEnabled(1)


    def activateWindow(self, index):
        """Activate the window selected from the Windows menu."""

        window = self.menuToWindowMap[index]
        self.raiseView(window)


    def raiseView(self, view):
        """
        Give focus to a given view.

        When a view gets focus it becomes the active window of the
        workspace. After this call the widget will be visually in front of
        any overlapping sibling widgets.

        :Parameter view: the view being activated
        """

        # QWidget.raiseW() is not used, see QWorkspace docs for details
        if view.isActiveWindow():
            # Give an activated look to the window
            # See docstring of the synchronizeWorkspace method for details
            qt.qApp.sendEvent(view, qt.QEvent(qt.QEvent.WindowActivate))
            self.otLV.setSelected(view.leaf_view.lvitem, True)
        else:
            view.setActiveWindow()  # This triggers slotSynchronizeTreeView
        view.setFocus()


    def slotSynchronizeTreeView(self, active_window):
        """
        Synchronize the tree view pane and the workspace.

        The driven force is state of the workspace. The node tied to the
        active view is selected.
        """

        # The WindowActivate SIGNAL can be emited with None widgets 
        if not active_window:
            return

        # zoom views are not synchronized
        if not isinstance(active_window, hpTable.HPTable):
            return

        # Select the item tied to the window being activated
        active_view = active_window.leaf_view
        self.otLV.ensureItemVisible(active_view.lvitem)
        self.otLV.setSelected(active_view.lvitem, True)
        # Give keyboard focus to the view
        active_window.setFocus()


    def slotWindowsClose(self):
        """Close the active window."""

        window = self.workspace.activeWindow()
        # generate a QCloseEvent that will be processed with the eventFilter
        window.close()


    def slotWindowsCloseAll(self):
        """Close all open windows."""

        for window in self.workspace.windowList(qt.QWorkspace.CreationOrder):
        # generate a QCloseEvent that will be processed with the eventFilter
            window.close()

    #
    # slot functions that handle user input: Tools menu #######################
    #
    def slotToolsLineUp(self):
        """Line up toolbars within visible dock areas as compactly as possible."""
        self.gui.lineUpDockWindows()


    def slotToolsHideToolBar(self):
        """
        Show/hide a given toolbar.

        Toolbar visibility depends on the state of the checkable
        ``Tools --> Toolbar... --> XXX`` menu item
        If the item is checked then the toolbar is shown,
        if the item is unchecked the toolbar is hidden.
        """

        # The object that sent the signal connected to this slot
        senderAction =  qt.QObject().sender()

        menuText = senderAction.menuText().latin1()
        if menuText == self.__tr('&File', 'Tools menu File entry'):
            pos = 0
            toolbar = self.gui.fileToolBar
        elif menuText == self.__tr('&Node', 'Tools menu Node entry'):
            pos = 1
            toolbar = self.gui.nodeToolBar
        elif menuText == self.__tr('&Help', 'Tools menu Help entry'):
            pos = 2
            toolbar = self.gui.helpToolBar

        # The Hide toolbar menu item ID
        id = self.gui.hideToolBarSubmenu.idAt(pos)
        if not self.gui.hideToolBarSubmenu.isItemChecked(id):
            # Show the hidden toolbar
            toolbar.show()
            self.gui.hideToolBarSubmenu.setItemChecked(id, 1)
        else:
            # Hide the shown toolbar
            toolbar.hide()
            self.gui.hideToolBarSubmenu.setItemChecked(id, 0)


    def slotToolsPreferences(self):
        """
        Launch the Preferences dialog.

        Clicking the ``OK`` button applies the configuration set in the
        Preferences dialog.
        Clicking the ``Cancel`` button re-applies the current
        configuration. This way any possible change tested with the
        ``Apply`` or ``Default`` button is reverted.
        """

        current_preferences = self.getPreferences()
        prefs =  preferences.Preferences(self, current_preferences)
        try:
            prefs.gui.exec_loop()
            # When OK is clicked then the new preferences are applied
            # via Preferences.slotApplyButton so nothing has to be done
            # here.
            # When Cancel is clicked then the preferences that were in
            # use when the dialog was called are reloaded.
            if prefs.gui.result() != qt.QDialog.Accepted:
                self.applyPreferences(current_preferences)
        finally:
            del prefs


    def getPreferences(self):
        """
        Get the preferences currently used by the application.

        The preferences is the subset of application settings that
        can be set via the Preferences dialog.
        
        :Returns: a dictionary with the current preferences
        """

        preferences = {
            'Logger/paper': self.logger.paper(),
            'Logger/text': self.logger.color(),
            'Logger/font': self.logger.font(),
            'Workspace/background': self.workspace.eraseColor(),
            'Look/currentStyle': self.currentStyle,
            'Startup/startupWorkingDirectory': self.startupWorkingDirectory,
            'Startup/restoreLastSession': self.restore_last_session, 
        }

        return preferences


    def applyPreferences(self, preferences):
        """
        Apply a given set of preferences.

        The preferences is the subset of application settings that
        can be set via the Preferences dialog.
        Beware that the logger paper setting must be converted to a QBrush
        instance.

        :Parameter preferences: a dictionary with the preferences to be applied
        """

        # Logger
        self.logger.setPaper(qt.QBrush(preferences['Logger/paper']))
        self.logger.setColor(preferences['Logger/text'])
        self.logger.setFont(preferences['Logger/font'])
        # Workspace
        self.workspace.setEraseColor(preferences['Workspace/background'])
        # Style
        self.currentStyle = preferences['Look/currentStyle']
        if self.currentStyle == 'default':
            qt.qApp.setStyle(self.config.default_style)
        else:
            qt.qApp.setStyle(self.currentStyle)
        # Startup
        self.startupWorkingDirectory = \
            preferences['Startup/startupWorkingDirectory']
        self.restore_last_session = preferences['Startup/restoreLastSession']
        # We must refresh the content of the logger in order to see
        # changes in text font/color
        loggerText = self.logger.text()
        self.logger.clear()
        self.logger.insert(loggerText)


    def getConfiguration(self):
        """
        Get the configuration currently used by the application.

        :Returns: a dictionary with the current configuration
        """

        p = self.gui.geometry()
        position = [p.x(), p.y(), p.width(), p.height()]
        configuration = self.getPreferences()
        configuration['Geometry/position'] = position
        configuration['Geometry/hsplitter'] = self.gui.hsplitter.sizes()
        configuration['Geometry/vsplitter'] = self.gui.vsplitter.sizes()
        configuration['Startup/lastWorkingDirectory'] = self.lastWorkingDirectory
        configuration['Recent/files'] = self.recentFilesList
        configuration['Session/files'] = self.getSessionFilesNodes()
        configuration['HelpBrowser/history'] = self.hbHistory
        configuration['HelpBrowser/bookmarks'] = self.hbBookmarks

        return configuration


    def saveConfiguration(self):
        """
        Store current application settings on disk.

        Note that we are using ``QSettings`` for writing to the config file,
        so we **must** rely on its searching algorithms in order to find
        that file. When a ``QSettings`` write method is invoqued, it
        traverses the following directories searching for the config
        file:

        - $QTDIR/etc/settings
        - $HOME/.vitables
        - $HOME/.qt

        and writes to the **first** config file found on which it has writing
        permissions. So, if we want to use $HOME/.vitables we must be
        sure that  there is not a writable config file in
        $QTDIR/etc/settings
        """

        configuration = self.getConfiguration()
        for (subkey, value) in configuration.items():
            self.config.writeProperty(subkey, value)
        # The QSettings instances MUST be destroyed in order to flush
        # changes to disk
        del self.config
        # so we have to create it again
        self.config = vtconfig.Config()


    def getSessionFilesNodes(self):
        """
        The list of files and nodes currently open.

        The current session state is grabbed from the tracking
        dictionaries managed by the leaves manager and the db manager.
        The list looks like::

            ['filepath1#@#mode#@#nodepath1#@#nodepath2, ...',
            'filepath2#@#mode#@#nodepath1#@#nodepath2, ...', ...]
        """

        # The files list returned by dbList does not include the temporary file
        sessionFilesNodes = {}
        for dbpath in self.dbManager.dbList():
            database = self.dbManager.getDB(dbpath)
            mode = database.getFileMode()
            # If a new file has been created during the current session
            # then write mode must be replaced by append mode or the file
            # will be created from scratch in the next ViTables session
            if mode == 'w':
                mode = 'a'
            sessionFilesNodes[database.filepath] = [mode]

        # [filePath#@#nodePath, filePath#@#nodePath, ...]
        # The files list returned by dbList includes views from temporary file
        for item in self.leavesManager.viewList():
            filepath, nodepath = item.split('#@#')
            if sessionFilesNodes.has_key(filepath):
                sessionFilesNodes[filepath].append(nodepath)

        # Convert the dictionary into a list
        session_files_nodes = \
            [str([key] + value)[1:-1].replace(', ', '#@#').replace("'", '') \
            for (key, value) in sessionFilesNodes.items()]

        # Format the list in a handy way to store it on disk
        return session_files_nodes


    #
    # slot functions that handle user input: Help menu ########################
    #


    def slotHelpDocBrowser(self):
        """
        Open the documentation browser

        Help --> UsersGuide
        """

        browser = helpBrowser.HelpBrowser(self)
        self.docBrowsers.append(browser)


    def slotHelpAbout(self):
        """
        Show a tabbed dialog with the application About and License info.

        Help --> About
        """

        # Text to be displayed
        aboutText = self.__tr(
            """<qt>
            <h3>ViTables %s</h3>
            ViTables is a graphical tool for displaying datasets
            stored in PyTables and hdf5 files. It is written using PyQt
            , the Python bindings for the Qt GUI toolkit.<p>
            For more information see
            <b>http://www.vitables.org</b>.<p>
            Please send bug reports or feature requests to the ViTables
            mailing list.<p>
            ViTables uses third party software which is copyrighted by
            its respective copyright holder. For details see the
            copyright notice of the individual packages.
            </qt>""",
            'Text of the About ViTables dialog')  % vtconfig.getVersion()
        licenseText = vitables.utils.getLicense()

        # Construct the dialog
        aboutDlg = qt.QTabDialog(self.gui)
        aboutDlg.setCaption(\
            self.__tr('About ViTables %s',
            'Caption of the About ViTables dialog') % vtconfig.getVersion())

        # Make About page
        aroot = qt.QWidget(aboutDlg)
        alayout = qt.QVBoxLayout(aroot, 10, 6)
        aboutEdit = qt.QTextEdit(aroot)
        aboutEdit.setReadOnly(1)
        aboutEdit.setTextFormat(qt.Qt.RichText)
        aboutEdit.setText(aboutText)
        alayout.addWidget(aboutEdit)
        hfw = aboutEdit.heightForWidth(180)
        aboutDlg.addTab(aroot, self.__tr('&About...',
            'Title of the first tab of the About dialog'))

        # Make License page
        lroot = qt.QWidget(aboutDlg)
        llayout = qt.QVBoxLayout(lroot, 10, 6)
        licenseEdit = qt.QTextEdit(lroot)
        licenseEdit.setReadOnly(1)
        licenseEdit.setTextFormat(qt.Qt.RichText)
        licenseEdit.setText(licenseText)
        llayout.addWidget(licenseEdit)
        aboutDlg.addTab(lroot, self.__tr('&License',
            'Title of the second tab of the About dialog'))

        aboutDlg.setOkButton(self.__tr('OK', 'A button label'))

        # Show the dialog
        aboutDlg.resize(380, hfw)
        aboutDlg.show()


    def slotHelpAboutQt(self):
        """
        Shows a message box with the Qt About info.

        Help --> About Qt
        """

        qt.QMessageBox.aboutQt(self.gui, self.__tr('About Qt',
            'Caption of the About Qt dialog'))


    def slotHelpVersions(self):
        """
        Message box with info about versions of libraries used by
        ViTables.

        Help --> Show Versions
        """

        # The libraries versions dictionary
        libsVersions = {
            'title': self.__tr('Version Numbers',
                'Caption of the Versions dialog'),
            'Python': reduce(lambda x,y: '.'.join([str(x), str(y)]),
                sys.version_info[:3]),
            'PyTables': tables.__version__ ,
            'NumPy': tables.numpy.__version__,
            'Qt': qt.qVersion(),
            'PyQt': qt.PYQT_VERSION_STR,
            'ViTables': vtconfig.getVersion()
        }

        # Add new items to the dictionary
        libraries = ('HDF5', 'Zlib', 'LZO', 'BZIP2')
        for lib in libraries:
            lversion = tables.whichLibVersion(lib.lower())
            if lversion:
                (mlv, version, date) = lversion
                libsVersions[lib] = version
            else:
                libsVersions[lib] = self.__tr('not available',
                    'Part of the library not found text')

        # Construct the dialog
        versionsDlg = qt.QTabDialog(self.gui)
        versionsDlg.setCaption(\
            self.__tr('Version Numbers','Caption of the Versions dialog'))

        # Make About page
        aroot = qt.QWidget(versionsDlg)
        alayout = qt.QVBoxLayout(aroot, 10, 6)
        versionsBox = qt.QTextEdit(aroot)
        versionsBox.setReadOnly(1)
        versionsBox.setText(\
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
            </qt>""" % libsVersions)
        alayout.addWidget(versionsBox)
        hfw = versionsBox.heightForWidth(100)
        versionsDlg.addTab(aroot, self.__tr('',
            'Title of the first tab of the About dialog'))
        # There is only one page. We remove its tab for visual clarity
        tabBar = versionsDlg.tabBar()
        tab = tabBar.currentTab()
        tabBar.removeTab(tabBar.tabAt(tabBar.currentTab()))

        # Show the dialog
        versionsDlg.resize(250, hfw)
        versionsDlg.show()

