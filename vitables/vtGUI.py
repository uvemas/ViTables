# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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

"""
This module provides de `ViTables` GUI: main window, menus, context menus, 
toolbars, statusbars and `QActions` bound to both menus and toolbars.
"""

__docformat__ = 'restructuredtext'
_context = 'VTGUI'

from PyQt4 import QtCore, QtGui

import vitables.utils
import vitables.logger as logger
import vitables.vtsplash



def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class VTGUI(QtGui.QMainWindow):
    """
    The application GUI.

    :Parameters:
        - `vtapp`: an instance of the :meth:`vitables.vtapp.VTApp` class
        - `version`: the `ViTables` version
    """


    def __init__(self, vtapp, version):
        """Initialize the application main window."""

        super(VTGUI, self).__init__(None)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(trs('ViTables %s' % version, 'Main window title'))
        self.vtapp = vtapp

        # Make the main window easily accessible for external modules
        self.setObjectName('VTGUI')

        self.icons_dictionary = vitables.utils.getIcons()


    def setup(self, tree_view):
        """Add widgets, actions, menus and toolbars to the GUI.

        :Parameter tree_view: The databases tree view
        """

        self.dbs_tree_view = tree_view
        self.dbs_tree_model = self.dbs_tree_view.model()
        self.addComponents()
        self.gui_actions = self.setupActions()
        self.setupToolBars()
        self.setupMenus()
        self.initStatusBar()

        self.logger.nodeCopyAction = self.gui_actions['nodeCopy']

        # Redirect standard output and standard error to a Logger instance
    #    sys.stdout = self.logger
    #    sys.stderr = self.logger


    def addComponents(self):
        """Add widgets to the main window.

        The main window contains a databases tree view, a workspace and a 
        console.
        """

        self.setIconSize(QtCore.QSize(22, 22))
        self.setWindowIcon(self.icons_dictionary['vitables_wm'])
        central_widget = QtGui.QWidget(self)
        central_layout = QtGui.QVBoxLayout(central_widget)
        self.vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical, central_widget)
        central_layout.addWidget(self.vsplitter)
        self.setCentralWidget(central_widget)

        # Divide the top region of the window into 2 regions and put there
        # the workspace. The tree of databases will be added later on
        self.hsplitter = QtGui.QSplitter(self.vsplitter)
        self.hsplitter.addWidget(self.dbs_tree_view)
        self.workspace = QtGui.QMdiArea(self.hsplitter)
        sb_as_needed = QtCore.Qt.ScrollBarAsNeeded
        self.workspace.setHorizontalScrollBarPolicy(sb_as_needed)
        self.workspace.setVerticalScrollBarPolicy(sb_as_needed)
        self.workspace.setWhatsThis(trs(
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

        # Put the logging console in the bottom region of the window
        self.logger = logger.Logger(self.vsplitter)

        # The signal mapper used to keep the the Window menu updated
        self.window_mapper = QtCore.QSignalMapper(self)
    #    self.window_mapper.mapped[QtGui.QWidget].connect(\
        self.window_mapper.mapped[QtGui.QWidget].connect(\
            self.workspace.setActiveSubWindow)

        self.workspace.installEventFilter(self)



    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        # Setting action names makes it easier to acces this actions
        # from plugins
        actions = {}
        actions['fileNew'] = QtGui.QAction(
            trs('&New', 'File -> New'), self, 
            shortcut=QtGui.QKeySequence.New, 
            triggered=self.vtapp.fileNew, 
            icon=self.icons_dictionary['document-new'], 
            statusTip=trs('Create a new file', 
                'Status bar text for the File -> New action'))
        actions['fileNew'].setObjectName('fileNew')

        actions['fileOpen'] = QtGui.QAction(
            trs('&Open...', 'File -> Open'), self, 
            shortcut=QtGui.QKeySequence.Open, 
            triggered=self.vtapp.fileOpen, 
            icon=self.icons_dictionary['document-open'], 
            statusTip=trs('Open an existing file',
                'Status bar text for the File -> Open action'))
        actions['fileOpen'].setObjectName('fileOpen')

        actions['fileOpenRO'] = QtGui.QAction(
            trs('Read-only open...', 'File -> Open'), self, 
            triggered=self.vtapp.fileOpenRO, 
            icon=self.icons_dictionary['document-open'], 
            statusTip=trs('Open an existing file in read-only mode',
                'Status bar text for the File -> Open action'))
        actions['fileOpenRO'].setObjectName('fileOpenRO')

        actions['fileClose'] = QtGui.QAction(
            trs('&Close', 'File -> Close'), self, 
            shortcut=QtGui.QKeySequence.Close, 
            triggered=self.vtapp.fileClose, 
            icon=self.icons_dictionary['document-close'], 
            statusTip=trs('Close the selected file',
                'Status bar text for the File -> Close action'))
        actions['fileClose'].setObjectName('fileClose')

        actions['fileCloseAll'] = QtGui.QAction(
            trs('Close &All', 'File -> Close All'), self, 
            triggered=self.vtapp.fileCloseAll, 
            statusTip=trs('Close all files', 
                'Status bar text for the File -> Close All action'))
        actions['fileCloseAll'].setObjectName('fileCloseAll')

        actions['fileSaveAs'] = QtGui.QAction(
            trs('&Save as...', 'File -> Save As'), self, 
            shortcut=QtGui.QKeySequence('CTRL+SHIFT+S'), 
            triggered=self.vtapp.fileSaveAs, 
            icon=self.icons_dictionary['document-save-as'], 
            statusTip=trs('Save a renamed copy of the selected file',
                'Status bar text for the File -> Save As action'))
        actions['fileSaveAs'].setObjectName('fileSaveAs')

        actions['fileExit'] = QtGui.QAction(
            trs('E&xit', 'File -> Exit'), self, 
            shortcut=QtGui.QKeySequence('CTRL+Q'), 
    #        triggered=self.vtapp.fileExit, 
            triggered=self.close, 
            icon=self.icons_dictionary['application-exit'], 
            statusTip=trs('Quit ViTables',
                'Status bar text for the File -> Exit action'))
        actions['fileExit'].setObjectName('fileExit')

        actions['nodeOpen'] = QtGui.QAction(
            trs('&Open view', 'Node -> Open View'), self, 
            shortcut=QtGui.QKeySequence('CTRL+SHIFT+O'), 
            triggered=self.vtapp.nodeOpen, 
            statusTip=trs('Display the contents of the selected node', 
                'Status bar text for the Node -> Open View action'))
        actions['nodeOpen'].setObjectName('nodeOpen')

        actions['nodeClose'] = QtGui.QAction(
            trs('C&lose view', 'Node -> Close View'), self, 
            shortcut=QtGui.QKeySequence('CTRL+SHIFT+W'), 
            triggered=self.vtapp.nodeClose, 
            statusTip=trs('Close the view of the selected node', 
                'Status bar text for the Node -> Close View action'))
        actions['nodeClose'].setObjectName('nodeClose')

        actions['nodeProperties'] = QtGui.QAction(
            trs('Prop&erties...', 'Node -> Properties'), self, 
            shortcut=QtGui.QKeySequence('CTRL+I'), 
            triggered=self.vtapp.nodeProperties, 
            icon=self.icons_dictionary['help-about'], 
            statusTip=trs('Show the properties dialog for the selected node', 
                'Status bar text for the Node -> Properties action'))
        actions['nodeProperties'].setObjectName('nodeProperties')

        actions['nodeNew'] = QtGui.QAction(
            trs('&New group...', 'Node -> New group'), self, 
            shortcut=QtGui.QKeySequence('CTRL+SHIFT+N'), 
            triggered=self.vtapp.nodeNewGroup, 
            icon=self.icons_dictionary['folder-new'], 
            statusTip=trs('Create a new group under the selected node', 
                'Status bar text for the Node -> New group action'))
        actions['nodeNew'].setObjectName('nodeNew')

        actions['nodeRename'] = QtGui.QAction(
            trs('&Rename...', 'Node -> Rename'), self, 
            shortcut=QtGui.QKeySequence('CTRL+R'), 
            triggered=self.vtapp.nodeRename, 
            icon=self.icons_dictionary['edit-rename'], 
            statusTip=trs('Rename the selected node', 
                'Status bar text for the Node -> Rename action'))
        actions['nodeRename'].setObjectName('nodeRename')

        actions['nodeCut'] = QtGui.QAction(
            trs('Cu&t', 'Node -> Cut'), self, 
            shortcut=QtGui.QKeySequence('CTRL+X'), 
            triggered=self.vtapp.nodeCut, 
            icon=self.icons_dictionary['edit-cut'], 
            statusTip=trs('Cut the selected node', 
                'Status bar text for the Node -> Cut action'))
        actions['nodeCut'].setObjectName('nodeCut')

        actions['nodeCopy'] = QtGui.QAction(
            trs('&Copy', 'Node -> Copy'), self, 
            shortcut=QtGui.QKeySequence.Copy, 
            triggered=self.makeCopy, 
            icon=self.icons_dictionary['edit-copy'], 
            statusTip=trs('Copy the selected node', 
                'Status bar text for the Node -> Copy action'))
        actions['nodeCopy'].setObjectName('nodeCopy')

        actions['nodePaste'] = QtGui.QAction(
            trs('&Paste', 'Node -> Paste'), self, 
            shortcut=QtGui.QKeySequence.Paste, 
            triggered=self.vtapp.nodePaste, 
            icon=self.icons_dictionary['edit-paste'], 
            statusTip=trs('Paste the last copied/cut node', 
                'Status bar text for the Node -> Copy action'))
        actions['nodePaste'].setObjectName('nodePaste')

        actions['nodeDelete'] = QtGui.QAction(
            trs('&Delete', 'Node -> Delete'), self, 
            shortcut=QtGui.QKeySequence.Delete, 
            triggered=self.vtapp.nodeDelete, 
            icon=self.icons_dictionary['edit-delete'], 
            statusTip=trs('Delete the selected node', 
                'Status bar text for the Node -> Copy action'))
        actions['nodeDelete'].setObjectName('nodeDelete')

        actions['queryNew'] = QtGui.QAction(
            trs('&Query...', 'Query -> New...'), self, 
            triggered=self.vtapp.newQuery, 
            icon=self.icons_dictionary['view-filter'], 
            statusTip=trs('Create a new filter for the selected table', 
                'Status bar text for the Query -> New... action'))
        actions['queryNew'].setObjectName('queryNew')

        actions['queryDeleteAll'] = QtGui.QAction(
            trs('Delete &All', 'Query -> Delete All'), self, 
            triggered=self.vtapp.deleteAllQueries, 
            icon=self.icons_dictionary['delete_filters'], 
            statusTip=trs('Remove all filters', 
                'Status bar text for the Query -> Delete All action'))
        actions['queryDeleteAll'].setObjectName('queryDeleteAll')

        actions['settingsPreferences'] = QtGui.QAction(
            trs('&Preferences...', 'Settings -> Preferences'), self, 
            triggered=self.vtapp.settingsPreferences, 
            icon=self.icons_dictionary['configure'], 
            statusTip=trs('Configure ViTables', 
                'Status bar text for the Settings -> Preferences action'))
        actions['settingsPreferences'].setObjectName('settingsPreferences')

        actions['windowCascade'] = QtGui.QAction(
            trs('&Cascade', 'Windows -> Cascade'), self, 
            triggered=self.workspace.cascadeSubWindows, 
            statusTip=trs('Arranges open windows in a cascade pattern', 
                'Status bar text for the Windows -> Cascade action'))
        actions['windowCascade'].setObjectName('windowCascade')

        actions['windowTile'] = QtGui.QAction(
            trs('&Tile', 'Windows -> Tile'), self, 
            triggered=self.workspace.tileSubWindows, 
            statusTip=trs('Arranges open windows in a tile pattern', 
                'Status bar text for the Windows -> Tile action'))
        actions['windowTile'].setObjectName('windowTile')

        actions['windowRestoreAll'] = QtGui.QAction(
            trs('&Restore All', 'Windows -> Restore All'), self, 
            triggered=self.vtapp.windowRestoreAll, 
            statusTip=trs('Restore all minimized windows on the workspace', 
                'Status bar text for the Windows -> Restore All action'))
        actions['windowRestoreAll'].setObjectName('windowRestoreAll')

        actions['windowMinimizeAll'] = QtGui.QAction(
            trs('&Minimize All', 'Windows -> Minimize All'), self, 
            triggered=self.vtapp.windowMinimizeAll, 
            statusTip=trs('Minimize all windows on the workspace', 
                'Status bar text for the Windows -> Restore All action'))
        actions['windowMinimizeAll'].setObjectName('windowMinimizeAll')

        actions['windowClose'] = QtGui.QAction(
            trs('C&lose', 'Windows -> Close'), self, 
            triggered=self.vtapp.windowClose, 
            statusTip=trs('Close the active view', 
                'Status bar text for the Windows -> Close action'))
        actions['windowClose'].setObjectName('windowClose')

        actions['windowCloseAll'] = QtGui.QAction(
            trs('Close &All', 'Windows -> Close All'), self, 
            triggered=self.vtapp.windowCloseAll, 
            statusTip=trs('Close all views', 
                'Status bar text for the Windows -> Close All action'))
        actions['windowCloseAll'].setObjectName('windowCloseAll')

        actions['windowSeparator'] = QtGui.QAction(
            trs('Current View', 'Windows -> separator'), self)
        actions['windowSeparator'].setSeparator(True)

        actions['mdiTabbed'] = QtGui.QAction(
            trs('Change view mode', 'MDI -> Tabbed'), self, 
            triggered=self.changeMDIViewMode, 
            statusTip=trs('Change the workspace view mode', 
                'Status bar text for the MDI -> Tabbed action'))
        actions['mdiTabbed'].setObjectName('mdiTabbed')

        actions['helpUsersGuide'] = QtGui.QAction(
            trs("&User's Guide", 'Help -> Users Guide'), self, 
            shortcut=QtGui.QKeySequence.HelpContents, 
            triggered=self.vtapp.helpBrowser, 
            icon=self.icons_dictionary['help-contents'], 
            statusTip=trs("Open the ViTables User's Guide",
                    'Status bar text for the Help -> Users Guide action'))
        actions['helpUsersGuide'].setObjectName('helpUsersGuide')

        actions['helpAbout'] = QtGui.QAction(
            trs('&About ViTables', 'Help -> About'), self, 
            triggered=self.vtapp.helpAbout, 
            icon=self.icons_dictionary['vitables_wm'], 
            statusTip=trs('Display information about ViTables',
                    'Status bar text for the Help -> About action'))
        actions['helpAbout'].setObjectName('helpAbout')

        actions['helpAboutQt'] = QtGui.QAction(
            trs('About &Qt', 'Help -> About Qt'), self, 
            triggered=self.vtapp.helpAboutQt, 
            statusTip=trs('Display information about the Qt library',
                    'Status bar text for the Help -> About Qt action'))
        actions['helpAboutQt'].setObjectName('helpAboutQt')

        actions['helpVersions'] = QtGui.QAction(
            trs('Show &Versions', 'Help -> Show Versions'), self, 
            triggered=self.vtapp.helpVersions, 
            statusTip=trs(\
                'Show the versions of the libraries used by ViTables', 
                'Status bar text for the Help -> Show Versions action'))
        actions['helpVersions'].setObjectName('helpVersions')

        return actions


    def setupToolBars(self):
        """
        Set up the main window toolbars.

        Toolbars are made of actions.
        """

        # File toolbar
        self.file_toolbar = self.addToolBar(trs('File operations', 
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
        file_open_button.setToolTip(trs("""Click to open a """
            """file\nClick and hold to open a recent file""",
            'File toolbar -> Open Recent Files'))

        # Node toolbar
        self.node_toolbar = self.addToolBar(trs('Node operations', 
            'Toolbar title'))
        self.node_toolbar.setObjectName('Node toolbar')
        actions = ['nodeNew', 'nodeCut', 'nodeCopy', 'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.node_toolbar, actions, self.gui_actions)

        # Query toolbar
        self.query_toolbar = self.addToolBar(trs('Queries on tables', 
            'Toolbar title'))
        self.query_toolbar.setObjectName('Query toolbar')
        actions = ['queryNew', 'queryDeleteAll']
        vitables.utils.addActions(self.query_toolbar, actions, 
                                    self.gui_actions)

        # Help toolbar
        self.help_toolbar = self.addToolBar(trs('Help system', 
            'Toolbar title'))
        self.help_toolbar.setObjectName('Help toolbar')
        actions = ['helpUsersGuide']
        vitables.utils.addActions(self.help_toolbar, actions, self.gui_actions)
        whatis = QtGui.QWhatsThis.createAction(self.help_toolbar)
        whatis.setStatusTip(trs('Contextual help',
                    'Status bar text for the Help -> Whats This action'))
        self.help_toolbar.addAction(whatis)


    def initStatusBar(self):
        """Initialise the status bar."""

        status_bar = self.statusBar()
        self.sb_node_info = QtGui.QLabel(status_bar)
        self.sb_node_info.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, \
                                        QtGui.QSizePolicy.Minimum)
        status_bar.addPermanentWidget(self.sb_node_info)
        self.sb_node_info.setToolTip(trs(
            'The node currently selected in the Tree of databases pane',
            'The Selected node box startup message'))
        status_bar.showMessage(trs('Ready...',
            'The status bar startup message'))


    def setupMenus(self):
        """
        Set up the main window menus.

        Popus are made of actions, items and separators.
        The `Window` menu is a special case due to its dynamic nature. Its
        contents depend on the number of existing views.
        In order to track changes and keep updated the menu, it is reloaded
        every time it is about to be displayed.
        """

        # Create the File menu and add actions/submenus/separators to it
        self.file_menu = self.menuBar().addMenu(trs("&File", 
            'The File menu entry'))
        self.file_menu.setObjectName('file_menu')
        self.open_recent_submenu = QtGui.QMenu(trs('Open R&ecent Files',
            'File -> Open Recent Files'))
        self.open_recent_submenu.setObjectName('open_recent_submenu')
        self.open_recent_submenu.setSeparatorsCollapsible(False)
        self.open_recent_submenu.setIcon(\
            self.icons_dictionary['document-open-recent'])
        file_actions = ['fileNew', 'fileOpen', 'fileOpenRO', 
            self.open_recent_submenu, None, 'fileClose', 'fileCloseAll', None, 
            'fileSaveAs', None, 'fileExit']
        vitables.utils.addActions(self.file_menu, file_actions, 
            self.gui_actions)

        file_open_button = self.file_toolbar.widgetForAction(
            self.gui_actions['fileOpen'])
        file_open_button.setMenu(self.open_recent_submenu)
        self.open_recent_submenu.aboutToShow.connect(\
            self.updateRecentSubmenu)

        # Create the Node menu and add actions/submenus/separators to it
        node_menu = self.menuBar().addMenu(trs("&Node", 
            'The Node menu entry'))
        node_menu.setObjectName('node_menu')
        node_actions = ['nodeOpen', 'nodeClose', 'nodeProperties', None, 
            'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy', 'nodePaste', 
            'nodeDelete']
        vitables.utils.addActions(node_menu, node_actions, self.gui_actions)

        # Create the Dataset menu and add actions/submenus/separators to it
        self.dataset_menu = self.menuBar().addMenu(trs("&Dataset", 
            'The Dataset menu entry'))
        self.dataset_menu.setObjectName('dataset_menu')
        dataset_actions = ['queryNew', None]
        vitables.utils.addActions(self.dataset_menu, dataset_actions, 
            self.gui_actions)

        # Create the Settings menu and add actions/submenus/separators to it
        settings_menu = self.menuBar().addMenu(trs("&Settings", 
            'The Settings menu entry'))
        settings_menu.setObjectName('settings-menu')
        self.hide_toolbar_submenu = self.createPopupMenu()
        self.hide_toolbar_submenu.menuAction().setText(trs('ToolBars', 
                                                'Tools -> ToolBars action'))
        settings_actions = ['settingsPreferences', None, 
            self.hide_toolbar_submenu]
        vitables.utils.addActions(settings_menu, settings_actions, 
            self.gui_actions)

        # Create the Window menu and add actions/menus/separators to it
        self.windows_menu = self.menuBar().addMenu(trs("&Window", 
            'The Windows menu entry'))
        self.windows_menu.setObjectName('windows_menu')
        windows_actions = ['windowCascade', 'windowTile', 
                           'windowRestoreAll', 'windowMinimizeAll', 
                           'windowClose', 'windowCloseAll', 'windowSeparator']
        vitables.utils.addActions(self.windows_menu, windows_actions, 
                                    self.gui_actions)
        self.windows_menu.setSeparatorsCollapsible(True)
        action_group = QtGui.QActionGroup(self.windows_menu)
        self.windows_menu.action_group = action_group
        self.windows_menu.aboutToShow.connect(self.updateWindowMenu)

        # Create the Help menu and add actions/menus/separators to it
        help_menu = self.menuBar().addMenu(trs("&Help", 
            'The Help menu entry'))
        help_menu.setObjectName('help_menu')
        help_actions = ['helpUsersGuide', None, 'helpAbout', 'helpAboutQt', 
            'helpVersions', None]
        vitables.utils.addActions(help_menu, help_actions, self.gui_actions)
        whatis = QtGui.QWhatsThis.createAction(help_menu)
        whatis.setStatusTip(trs('Context help',
                    'Status bar text for the Help -> Whats This action'))
        help_menu.addAction(whatis)

        #########################################################
        #
        # 				Context menus
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


    def closeEvent(self, event):
        """
        Handle close events.

        Clicking the close button of the main window titlebar causes
        the application quitting immediately, leaving things in a non
        consistent state. This event handler ensures that the needed
        tidy up is done before quitting.

        :Parameter event: the close event being handled
        """

        # Do the required tidy up
        self.vtapp.fileExit()

        # Quit
        event.accept()
        QtGui.qApp.quit()


    def makeCopy(self):
        """Copy text/leaf depending on which widget has focus.

        This methos disambiguates the ``Ctrl+C`` shortcut. If the console has focus
        then ``Ctrl+C`` will copy the console selected text. If the databases tree
        view has focus then the selected node (if any) will be copied.
        """

        if self.dbs_tree_view.hasFocus():
            self.vtapp.nodeCopy()
        elif self.logger.hasFocus():
            self.logger.copy()

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

    def updateActions(self):
        """
        Update the state of the actions tied to menu items and toolbars.

        Every time that the selected item changes in the tree viewer the
        state of the actions must be updated because it depends on the
        type of selected item (leaf or group, opening mode etc.).
        The following events trigger a call to this slot:

            * insertion/deletion of rows in the tree of databases model
            * changes in the selection state of the tree of databases view

        The slot should be manually called when a new view is activated in
        the workspace (for instance by methods 
        :meth:`vitables.vtapp.VTApp.nodeOpen`, 
        :meth:`vitables.vtapp.VTApp.nodeClose`).

        .. _Warning:

        Warning! Don\'t call this method until the GUI initialisation finishes.
        """

        # The following actions are always active:
        # fileNew, fileOpen, fileOpenRO, fileExit and the Help menu actions

        # The set of actions that can be enabled or disabled
        actions = frozenset(['fileClose', 'fileCloseAll', 'fileSaveAs', 
                            'nodeOpen', 'nodeClose', 'nodeProperties', 
                            'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy', 
                            'nodePaste', 'nodeDelete', 
                            'queryNew', 'queryDeleteAll'])
        enabled = set([])

        model_rows = self.dbs_tree_model.rowCount(QtCore.QModelIndex())
        if model_rows <= 0:
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


    def updateRecentSubmenu(self):
        """Update the content of the `Open Recent File...` submenu."""

        index = 0
        self.open_recent_submenu.clear()
        iconset = vitables.utils.getIcons()
        for item in self.vtapp.config.recent_files:
            index += 1
            (mode, filepath) = item.split('#@#')
            action = QtGui.QAction(u'%s. ' % index + filepath, self, 
                triggered=self.vtapp.openRecentFile)
            action.setData(QtCore.QVariant(item))
            if mode == 'r':
                action.setIcon(iconset['file_ro'])
            else:
                action.setIcon(iconset['file_rw'])
            self.open_recent_submenu.addAction(action)

        # Always add a separator and a clear QAction. So if the menu is empty
        # the user still will know what's going on
        self.open_recent_submenu.addSeparator()
        action = QtGui.QAction(trs('&Clear', 'Recent File submenu entry'), 
            self, triggered=self.vtapp.clearRecentFiles)
        self.open_recent_submenu.addAction(action)


    def updateWindowMenu(self):
        """
        Update the `Window` menu.

        The `Window` menu is dynamic because its content is determined
        by the currently open views. Because the number of these views or
        its contents may vary at any moment we must update the `Window`
        menu every time it is open. For simplicity we don't keep track
        of changes in the menu content. Instead, we clean and create it
        from scratch every time it is about to show.
        """

        menu = self.windows_menu
        windows_list = self.workspace.subWindowList()
        if not windows_list:
            return

        # Clear the existing views from the Window menu
        for action in menu.action_group.actions():
            menu.action_group.removeAction(action)
            menu.removeAction(action)

        # Reload the existing views
        counter = 1
        for window in windows_list:
            title = window.windowTitle()
            if counter == 10:
                menu.addSeparator()
                menu = menu.addMenu(trs("&More", 'A Windows submenu'))
            accel = ""
            if counter < 10:
                accel = "&%d " % counter
            elif counter < 36:
                accel = "&%c " % chr(counter + ord("@") - 9)
            action = menu.addAction("%s%s" % (accel, title))
            menu.action_group.addAction(action)
            action.setCheckable(True)
            if self.workspace.activeSubWindow() == window:
                action.setChecked(True)
            action.triggered.connect(self.window_mapper.map)
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
        Popup a context menu in the tree of databases view.

        When a point of the tree view is right clicked, a context
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
            wnodepath = window.dbt_leaf.nodepath
            wfilepath = window.dbt_leaf.filepath
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
        """Event filter used to provide the workspace with a context menu.

        :Parameters:

            - `widget`: the widget that receives the event
            - `event`: the event being processed
        """

        if widget == self.workspace:
            if event.type() == QtCore.QEvent.ContextMenu:
                pos = event.globalPos()
                self.mdi_cm.popup(pos)
            return QtGui.QMdiArea.eventFilter(widget, widget, event)
        else:
            return QtGui.QMainWindow.eventFilter(self, widget, event)
