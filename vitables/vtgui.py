#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
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

import logging
from vitables.calculator import calculator
import vitables.utils

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.h5db.dbstreemodel as dbstreemodel
import vitables.h5db.dbstreeview as dbstreeview
import vitables.logger as logger

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate

_GUI_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class VTGUI(QtWidgets.QMainWindow):
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
        self.setWindowTitle(translate('VTGUI', 'ViTables {0}',
                                      'Main window title').format(version))
        self.vtapp = vtapp

        # Make the main window easily accessible for external modules
        self.setObjectName('VTGUI')

        self.icons_dictionary = vitables.utils.getIcons()
        # After a node editing the workspace and the databases tree view
        # should not been sync because keyboard focus should remain on
        # the tree view. However, if editing dialogs are raised, when
        # they are closed the focus goes temporarily to the workspace,
        # resulting in spurious syncs. The editing_dlg flag prevents
        # this behavior
        self.editing_dlg = None
        self.logger_dock = None
        self.logger = None
        self.setup_logger_window()
        self.setup(vtapp)

    def setup(self, vtapp):
        """Add widgets, actions, menus and toolbars to the GUI.

        :Parameter tree_view: The databases tree view
        """

        self.dbs_tree_model = dbstreemodel.DBsTreeModel(self, vtapp)
        self.dbs_tree_view = dbstreeview.DBsTreeView(vtapp, self,
                                                     self.dbs_tree_model,
                                                     self)
        self.addComponents()
        self.gui_actions = self.setupActions()
        self.setupToolBars()
        self.setupMenus()
        self.initStatusBar()

        self.logger.nodeCopyAction = self.gui_actions['nodeCopy']

    def setup_logger_window(self):
        # Put the logging console in the bottom region of the window
        self.logger_dock = QtWidgets.QDockWidget('Log')
        self.logger_dock.setObjectName('LoggerDockWidget')
        self.logger_dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable
            | QtWidgets.QDockWidget.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.logger_dock)
        self.logger = logger.Logger(self)
        self.logger.setObjectName('LoggerWidget')
        self.logger_dock.setWidget(self.logger)
        # add self.logger as handler of main logger object
        vitables_logger = logging.getLogger('vitables')
        stream_handler = logging.StreamHandler(self.logger)
        stream_handler.setFormatter(logging.Formatter(_GUI_LOG_FORMAT))
        vitables_logger.addHandler(stream_handler)

    def addComponents(self):
        """Add widgets to the main window.

        The main window contains a databases tree view, a workspace and a
        console.

        """

        self.setIconSize(QtCore.QSize(22, 22))
        self.setWindowIcon(self.icons_dictionary['vitables_wm'])
        central_widget = QtWidgets.QWidget(self)
        central_layout = QtWidgets.QVBoxLayout(central_widget)
        # Divide the top region of the window into 2 regions and put there
        # the workspace. The tree of databases will be added later on
        self.hsplitter = QtWidgets.QSplitter(
            QtCore.Qt.Horizontal, central_widget)
        self.hsplitter.setObjectName('hsplitter')
        central_layout.addWidget(self.hsplitter)
        self.setCentralWidget(central_widget)
        self.hsplitter.addWidget(self.dbs_tree_view)
        self.workspace = QtWidgets.QMdiArea(self.hsplitter)
        sb_as_needed = QtCore.Qt.ScrollBarAsNeeded
        self.workspace.setHorizontalScrollBarPolicy(sb_as_needed)
        self.workspace.setVerticalScrollBarPolicy(sb_as_needed)
        self.workspace.setWhatsThis(
            translate('VTGUI',
                      """<qt>
                      <h3>The Workspace</h3>
                      This is the area where open leaves of the object tree are
                      displayed. Many tables and arrays can be displayed
                      simultaneously.
                      <p>The diferent views can be tiled as a mosaic or
                      stacked as a cascade.
                      </qt>""",
                      'WhatsThis help for the workspace'))

        # The signal mapper used to keep the the Window menu updated
        self.window_mapper = QtCore.QSignalMapper(self)
        self.window_mapper.mapped[QtWidgets.QWidget].connect(
            self.workspace.setActiveSubWindow)
        self.workspace.installEventFilter(self)
        self.dbs_tree_view.clicked.connect(self.selection_changed)

    def selection_changed(self, index):
        self.updateActions()
        self.updateStatusBar()

    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        # Setting action names makes it easier to acces these actions
        # from plugins
        actions = {}
        actions['fileNew'] = QtWidgets.QAction(
            translate('VTGUI', '&New...', 'File -> New'), self,
            shortcut=QtGui.QKeySequence.New,
            triggered=self.vtapp.fileNew,
            icon=self.icons_dictionary['document-new'],
            statusTip=translate(
                'VTGUI', 'Create a new file',
                'Status bar text for the File -> New action'))
        actions['fileNew'].setObjectName('fileNew')

        actions['fileOpen'] = QtWidgets.QAction(
            translate('VTGUI', '&Open...', 'File -> Open'), self,
            shortcut=QtGui.QKeySequence.Open,
            triggered=self.vtapp.fileOpen,
            icon=self.icons_dictionary['document-open'],
            statusTip=translate(
                'VTGUI', 'Open an existing file',
                'Status bar text for the File -> Open action'))
        actions['fileOpen'].setObjectName('fileOpen')

        actions['fileOpenRO'] = QtWidgets.QAction(
            translate('VTGUI', 'Read-only open...', 'File -> Open'), self,
            triggered=self.vtapp.fileOpenRO,
            icon=self.icons_dictionary['document-open'],
            statusTip=translate(
                'VTGUI', 'Open an existing file in read-only mode',
                'Status bar text for the File -> Open action'))
        actions['fileOpenRO'].setObjectName('fileOpenRO')

        actions['fileClose'] = QtWidgets.QAction(
            translate('VTGUI', '&Close', 'File -> Close'), self,
            shortcut=QtGui.QKeySequence('Shift+F4'),
            triggered=self.vtapp.fileClose,
            icon=self.icons_dictionary['document-close'],
            statusTip=translate(
                'VTGUI', 'Close the selected file',
                'Status bar text for the File -> Close action'))
        actions['fileClose'].setObjectName('fileClose')

        actions['fileCloseAll'] = QtWidgets.QAction(
            translate('VTGUI', 'Close &All', 'File -> Close All'), self,
            triggered=self.vtapp.fileCloseAll,
            statusTip=translate(
                'VTGUI', 'Close all files',
                'Status bar text for the File -> Close All action'))
        actions['fileCloseAll'].setObjectName('fileCloseAll')

        actions['fileSaveAs'] = QtWidgets.QAction(
            translate('VTGUI', '&Save as...', 'File -> Save As'), self,
            shortcut=QtGui.QKeySequence.SaveAs,
            triggered=self.vtapp.fileSaveAs,
            icon=self.icons_dictionary['document-save-as'],
            statusTip=translate(
                'VTGUI', 'Save a renamed copy of the selected file',
                'Status bar text for the File -> Save As action'))
        actions['fileSaveAs'].setObjectName('fileSaveAs')

        actions['fileExit'] = QtWidgets.QAction(
            translate('VTGUI', 'E&xit', 'File -> Exit'), self,
            shortcut=QtGui.QKeySequence.Quit,
            triggered=self.close,
            icon=self.icons_dictionary['application-exit'],
            statusTip=translate(
                'VTGUI', 'Quit ViTables',
                'Status bar text for the File -> Exit action'))
        actions['fileExit'].setObjectName('fileExit')

        actions['nodeOpen'] = QtWidgets.QAction(
            translate('VTGUI', '&Open view', 'Node -> Open View'), self,
            shortcut=QtGui.QKeySequence('Alt+Ctrl+O'),
            triggered=self.vtapp.nodeOpen,
            statusTip=translate(
                'VTGUI', 'Display the contents of the selected node',
                'Status bar text for the Node -> Open View action'))
        actions['nodeOpen'].setObjectName('nodeOpen')

        actions['nodeClose'] = QtWidgets.QAction(
            translate('VTGUI', 'C&lose view', 'Node -> Close View'), self,
            shortcut=QtGui.QKeySequence('Alt+Shift+F4'),
            triggered=self.vtapp.nodeClose,
            statusTip=translate(
                'VTGUI', 'Close the view of the selected node',
                'Status bar text for the Node -> Close View action'))
        actions['nodeClose'].setObjectName('nodeClose')

        actions['nodeProperties'] = QtWidgets.QAction(
            translate('VTGUI', 'Prop&erties...', 'Node -> Properties'), self,
            shortcut=QtGui.QKeySequence('Ctrl+I'),
            triggered=self.vtapp.nodeProperties,
            icon=self.icons_dictionary['help-about'],
            statusTip=translate(
                'VTGUI', 'Show the properties dialog for the selected node',
                'Status bar text for the Node -> Properties action'))
        actions['nodeProperties'].setObjectName('nodeProperties')

        actions['nodeNew'] = QtWidgets.QAction(
            translate('VTGUI', '&New group...', 'Node -> New group'), self,
            shortcut=QtGui.QKeySequence('Alt+Ctrl+N'),
            triggered=self.vtapp.nodeNewGroup,
            icon=self.icons_dictionary['folder-new'],
            statusTip=translate(
                'VTGUI', 'Create a new group under the selected node',
                'Status bar text for the Node -> New group action'))
        actions['nodeNew'].setObjectName('nodeNew')

        actions['nodeRename'] = QtWidgets.QAction(
            translate('VTGUI', '&Rename...', 'Node -> Rename'), self,
            shortcut=QtGui.QKeySequence('Ctrl+R'),
            triggered=self.vtapp.nodeRename,
            icon=self.icons_dictionary['edit-rename'],
            statusTip=translate(
                'VTGUI', 'Rename the selected node',
                'Status bar text for the Node -> Rename action'))
        actions['nodeRename'].setObjectName('nodeRename')

        actions['nodeCut'] = QtWidgets.QAction(
            translate('VTGUI', 'Cu&t', 'Node -> Cut'), self,
            shortcut=QtGui.QKeySequence.Cut,
            triggered=self.vtapp.nodeCut,
            icon=self.icons_dictionary['edit-cut'],
            statusTip=translate('VTGUI', 'Cut the selected node',
                                'Status bar text for the Node -> Cut action'))
        actions['nodeCut'].setObjectName('nodeCut')

        actions['nodeCopy'] = QtWidgets.QAction(
            translate('VTGUI', '&Copy', 'Node -> Copy'), self,
            shortcut=QtGui.QKeySequence.Copy,
            triggered=self.makeCopy,
            icon=self.icons_dictionary['edit-copy'],
            statusTip=translate('VTGUI', 'Copy the selected node',
                                'Status bar text for the Node -> Copy action'))
        actions['nodeCopy'].setObjectName('nodeCopy')

        actions['nodePaste'] = QtWidgets.QAction(
            translate('VTGUI', '&Paste', 'Node -> Paste'), self,
            shortcut=QtGui.QKeySequence.Paste,
            triggered=self.vtapp.nodePaste,
            icon=self.icons_dictionary['edit-paste'],
            statusTip=translate('VTGUI', 'Paste the last copied/cut node',
                                'Status bar text for the Node -> Copy action'))
        actions['nodePaste'].setObjectName('nodePaste')

        actions['nodeDelete'] = QtWidgets.QAction(
            translate('VTGUI', '&Delete', 'Node -> Delete'), self,
            shortcut=QtGui.QKeySequence.Delete,
            triggered=self.vtapp.nodeDelete,
            icon=self.icons_dictionary['edit-delete'],
            statusTip=translate('VTGUI', 'Delete the selected node',
                                'Status bar text for the Node -> Copy action'))
        actions['nodeDelete'].setObjectName('nodeDelete')

        actions['queryNew'] = QtWidgets.QAction(
            translate('VTGUI', '&Query...', 'Query -> New...'), self,
            triggered=self.vtapp.newQuery,
            icon=self.icons_dictionary['view-filter'],
            statusTip=translate(
                'VTGUI', 'Create a new filter for the selected table',
                'Status bar text for the Query -> New... action'))
        actions['queryNew'].setObjectName('queryNew')

        actions['queryDeleteAll'] = QtWidgets.QAction(
            translate('VTGUI', 'Delete &All', 'Query -> Delete All'), self,
            triggered=self.vtapp.deleteAllQueries,
            icon=self.icons_dictionary['delete_filters'],
            statusTip=translate(
                'VTGUI', 'Remove all filters',
                'Status bar text for the Query -> Delete All action'))
        actions['queryDeleteAll'].setObjectName('queryDeleteAll')

        actions['settingsPreferences'] = QtWidgets.QAction(
            translate('VTGUI', '&Preferences...', 'Settings -> Preferences'),
            self,
            shortcut=QtGui.QKeySequence.Preferences,
            triggered=self.vtapp.settingsPreferences,
            icon=self.icons_dictionary['configure'],
            statusTip=translate(
                'VTGUI', 'Configure ViTables',
                'Status bar text for the Settings -> Preferences action'))
        actions['settingsPreferences'].setObjectName('settingsPreferences')

        actions['windowCascade'] = QtWidgets.QAction(
            translate('VTGUI', '&Cascade', 'Windows -> Cascade'), self,
            triggered=self.workspace.cascadeSubWindows,
            statusTip=translate(
                'VTGUI', 'Arranges open windows in a cascade pattern',
                'Status bar text for the Windows -> Cascade action'))
        actions['windowCascade'].setObjectName('windowCascade')

        actions['windowTile'] = QtWidgets.QAction(
            translate('VTGUI', '&Tile', 'Windows -> Tile'), self,
            triggered=self.workspace.tileSubWindows,
            statusTip=translate(
                'VTGUI', 'Arranges open windows in a tile pattern',
                'Status bar text for the Windows -> Tile action'))
        actions['windowTile'].setObjectName('windowTile')

        actions['windowRestoreAll'] = QtWidgets.QAction(
            translate('VTGUI', '&Restore All', 'Windows -> Restore All'),
            self,
            triggered=self.vtapp.windowRestoreAll,
            statusTip=translate(
                'VTGUI', 'Restore all minimized windows on the workspace',
                'Status bar text for the Windows -> Restore All action'))
        actions['windowRestoreAll'].setObjectName('windowRestoreAll')

        actions['windowMinimizeAll'] = QtWidgets.QAction(
            translate('VTGUI', '&Minimize All', 'Windows -> Minimize All'),
            self,
            triggered=self.vtapp.windowMinimizeAll,
            statusTip=translate(
                'VTGUI', 'Minimize all windows on the workspace',
                'Status bar text for the Windows -> Restore All action'))
        actions['windowMinimizeAll'].setObjectName('windowMinimizeAll')

        actions['windowClose'] = QtWidgets.QAction(
            translate('VTGUI', 'C&lose', 'Windows -> Close'), self,
            triggered=self.vtapp.windowClose,
            statusTip=translate(
                'VTGUI', 'Close the active view',
                'Status bar text for the Windows -> Close action'))
        actions['windowClose'].setObjectName('windowClose')

        actions['windowCloseAll'] = QtWidgets.QAction(
            translate('VTGUI', 'Close &All', 'Windows -> Close All'), self,
            triggered=self.vtapp.windowCloseAll,
            statusTip=translate(
                'VTGUI', 'Close all views',
                'Status bar text for the Windows -> Close All action'))
        actions['windowCloseAll'].setObjectName('windowCloseAll')

        actions['windowSeparator'] = QtWidgets.QAction(
            translate('VTGUI', 'Current View', 'Windows -> separator'), self)
        actions['windowSeparator'].setSeparator(True)
        actions['windowSeparator'].setObjectName('windowSeparator')

        actions['mdiTabbed'] = QtWidgets.QAction(
            translate('VTGUI', 'Toggle MDI/Tabs', 'MDI -> Tabbed'), self,
            triggered=self.changeMDIViewMode,
            statusTip=translate(
                'VTGUI',
                'Toggle workspace view mode between Tabs <--> Multi Document '
                'Interface',
                'Status bar text for the MDI -> Tabbed action'))
        actions['mdiTabbed'].setObjectName('mdiTabbed')

        actions['helpUsersGuide'] = QtWidgets.QAction(
            translate('VTGUI', "&User's Guide", 'Help -> Users Guide'), self,
            shortcut=QtGui.QKeySequence.HelpContents,
            triggered=self.vtapp.helpBrowser,
            icon=self.icons_dictionary['help-contents'],
            statusTip=translate(
                'VTGUI', "Open the ViTables User's Guide",
                'Status bar text for the Help -> Users Guide action'))
        actions['helpUsersGuide'].setObjectName('helpUsersGuide')

        actions['helpAbout'] = QtWidgets.QAction(
            translate('VTGUI', '&About ViTables', 'Help -> About'), self,
            triggered=self.vtapp.helpAbout,
            icon=self.icons_dictionary['vitables_wm'],
            statusTip=translate(
                'VTGUI', 'Display information about ViTables',
                'Status bar text for the Help -> About action'))
        actions['helpAbout'].setObjectName('helpAbout')

        actions['helpAboutQt'] = QtWidgets.QAction(
            translate('VTGUI', 'About &Qt', 'Help -> About Qt'), self,
            triggered=self.vtapp.helpAboutQt,
            statusTip=translate(
                'VTGUI', 'Display information about the Qt library',
                'Status bar text for the Help -> About Qt action'))
        actions['helpAboutQt'].setObjectName('helpAboutQt')

        actions['helpVersions'] = QtWidgets.QAction(
            translate('VTGUI', 'Show &Versions', 'Help -> Show Versions'),
            self,
            triggered=self.vtapp.helpVersions,
            statusTip=translate(
                'VTGUI', 'Show the versions of the libraries used by ViTables',
                'Status bar text for the Help -> Show Versions action'))
        actions['helpVersions'].setObjectName('helpVersions')

        actions['calculate'] = QtWidgets.QAction(
            translate('VTGUI', 'Calculate...', 'Calculate action'),
            self,
            triggered=calculator.run,
            statusTip=translate(
                'VTGUI', 'Run calculation on opened tables.',
                'Action tip'))
        actions['calculate'].setObjectName('calculate')

        return actions

    def setupToolBars(self):
        """
        Set up the main window toolbars.

        Toolbars are made of actions.
        """

        # File toolbar
        self.file_toolbar = self.addToolBar(
            translate('VTGUI', 'File operations', 'Toolbar title'))
        # Warning! Do NOT use 'File toolbar' as a object name or it will
        # show an strange behaviour (a Qt bug I think): it will always
        # be added to the left and will expand the whole top area
        self.file_toolbar.setObjectName('File toolbar')
        actions = ['fileNew', 'fileOpen', 'fileClose', 'fileSaveAs']
        vitables.utils.addActions(self.file_toolbar, actions, self.gui_actions)

        # Reset the tooltip of the File -> Open... button
        file_open_button = self.file_toolbar.widgetForAction(
            self.gui_actions['fileOpen'])
        file_open_button.setToolTip(translate(
            'VTGUI', """Click to open a """
            """file\nClick and hold to open a recent file""",
            'File toolbar -> Open Recent Files'))

        # Node toolbar
        self.node_toolbar = self.addToolBar(
            translate('VTGUI', 'Node operations', 'Toolbar title'))
        self.node_toolbar.setObjectName('Node toolbar')
        actions = ['nodeNew', 'nodeCut', 'nodeCopy', 'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.node_toolbar, actions, self.gui_actions)

        # Query toolbar
        self.query_toolbar = self.addToolBar(
            translate('VTGUI', 'Queries on tables', 'Toolbar title'))
        self.query_toolbar.setObjectName('Query toolbar')
        actions = ['queryNew', 'queryDeleteAll']
        vitables.utils.addActions(self.query_toolbar, actions,
                                  self.gui_actions)

        # Help toolbar
        self.help_toolbar = self.addToolBar(translate('VTGUI', 'Help system',
                                                      'Toolbar title'))
        self.help_toolbar.setObjectName('Help toolbar')
        actions = ['helpUsersGuide']
        vitables.utils.addActions(self.help_toolbar, actions, self.gui_actions)
        whatis = QtWidgets.QWhatsThis.createAction(self.help_toolbar)
        whatis.setObjectName('whatis_help_toolbar')
        whatis.setStatusTip(translate(
            'VTGUI', 'Whats this? help for a widget',
            'Status bar text for the Help -> Whats This action'))
        whatis.setShortcut(QtGui.QKeySequence())
        self.help_toolbar.addAction(whatis)

    def initStatusBar(self):
        """Initialise the status bar."""

        status_bar = self.statusBar()
        self.sb_node_info = QtWidgets.QLabel(status_bar)
        self.sb_node_info.setObjectName('status bar widget')
        self.sb_node_info.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                        QtWidgets.QSizePolicy.Minimum)
        status_bar.addPermanentWidget(self.sb_node_info)
        self.sb_node_info.setToolTip(translate(
            'VTGUI', 'The node currently selected in the Tree of '
            'databases pane', 'The Selected node box startup message'))
        status_bar.showMessage(translate('VTGUI', 'Ready...',
                                         'The status bar startup message'))

    def setupMenus(self):
        """
        Set up the main window menus.

        Popups are made of actions, items and separators.
        The `Window` menu is a special case due to its dynamic nature. Its
        contents depend on the number of existing views.
        In order to track changes and keep updated the menu, it is reloaded
        every time it is about to be displayed.
        """

        # Create the File menu and add actions/submenus/separators to it
        self.file_menu = self.menuBar().addMenu(translate(
            'VTGUI', "&File", 'The File menu entry'))
        self.file_menu.setObjectName('file_menu')
        # The Open Recent submenu
        self.open_recent_submenu = QtWidgets.QMenu(
            translate('VTGUI', 'Open R&ecent Files',
                      'File -> Open Recent Files'))
        self.open_recent_submenu.setObjectName('open_recent_submenu')
        self.open_recent_submenu.setSeparatorsCollapsible(False)
        self.open_recent_submenu.setIcon(
            self.icons_dictionary['document-open-recent'])

        file_actions = ['fileNew', 'fileOpen', 'fileOpenRO',
                        self.open_recent_submenu, None, 'fileClose',
                        'fileCloseAll', None, 'fileSaveAs', None, 'fileExit']
        vitables.utils.addActions(self.file_menu, file_actions,
                                  self.gui_actions)

        file_open_button = self.file_toolbar.widgetForAction(
            self.gui_actions['fileOpen'])
        file_open_button.setMenu(self.open_recent_submenu)
        self.open_recent_submenu.aboutToShow.connect(self.updateRecentSubmenu)

        # Create the Node menu and add actions/submenus/separators to it
        self.node_menu = self.menuBar().addMenu(
            translate('VTGUI', "&Node", 'The Node menu entry'))
        self.node_menu.setObjectName('node_menu')
        node_actions = ['nodeOpen', 'nodeClose', 'nodeProperties', None,
                        'nodeNew', 'nodeRename', 'nodeCut', 'nodeCopy',
                        'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.node_menu, node_actions,
                                  self.gui_actions)

        # Create the Dataset menu and add actions/submenus/separators to it
        self.dataset_menu = self.menuBar().addMenu(
            translate('VTGUI', "&Dataset", 'The Dataset menu entry'))
        self.dataset_menu.setObjectName('dataset_menu')
        dataset_actions = ['queryNew', 'calculate']
        vitables.utils.addActions(self.dataset_menu, dataset_actions,
                                  self.gui_actions)

        # Create the Settings menu and add actions/submenus/separators to it
        settings_menu = self.menuBar().addMenu(
            translate('VTGUI', "&Settings", 'The Settings menu entry'))
        settings_menu.setObjectName('settings_menu')
        # Returns a popup menu containing checkable entries for the toolbars
        # and dock widgets present in the main window
        self.toolbars_submenu = self.createPopupMenu()
        self.toolbars_submenu.setObjectName('settings_toolbars_submenu')
        self.toolbars_submenu.menuAction().setText(
            translate('VTGUI', 'ToolBars', 'Tools -> ToolBars action'))
        settings_actions = ['settingsPreferences', None,
                            self.toolbars_submenu]
        vitables.utils.addActions(settings_menu, settings_actions,
                                  self.gui_actions)

        # Create the Window menu and add actions/menus/separators to it
        self.window_menu = self.menuBar().addMenu(
            translate('VTGUI', "&Window", 'The Windows menu entry'))
        self.window_menu.setObjectName('window_menu')
        windows_actions = ['windowCascade', 'windowTile',
                           'windowRestoreAll', 'windowMinimizeAll',
                           'windowClose', 'windowCloseAll', None, 'mdiTabbed',
                           'windowSeparator']
        vitables.utils.addActions(self.window_menu, windows_actions,
                                  self.gui_actions)
        self.window_menu.setSeparatorsCollapsible(True)
        self.window_menu.aboutToShow.connect(self.updateWindowMenu)

        # Create the Help menu and add actions/menus/separators to it
        help_menu = self.menuBar().addMenu(
            translate('VTGUI', "&Help", 'The Help menu entry'))
        help_menu.setObjectName('help_menu')
        help_actions = ['helpUsersGuide', None, 'helpAbout', 'helpAboutQt',
                        'helpVersions', None]
        vitables.utils.addActions(help_menu, help_actions, self.gui_actions)
        whatis = QtWidgets.QWhatsThis.createAction(help_menu)
        whatis.setObjectName('whatis_help_menu')
        whatis.setStatusTip(
            translate('VTGUI', 'Context help',
                      'Status bar text for the Help -> Whats This action'))
        help_menu.addAction(whatis)

        #########################################################
        #
        # 				Context menus
        #
        #########################################################

        self.view_cm = QtWidgets.QMenu(self)
        self.view_cm.setObjectName('view_cm')
        actions = ['fileNew', 'fileOpen', 'fileOpenRO',
                   self.open_recent_submenu, None, 'fileClose',
                   'fileCloseAll', None, 'fileSaveAs', None, 'fileExit']
        vitables.utils.addActions(self.view_cm, actions, self.gui_actions)

        self.root_node_cm = QtWidgets.QMenu(self)
        self.root_node_cm.setObjectName('root_node_cm')
        actions = ['fileClose', 'fileSaveAs', None, 'nodeProperties', None,
                   'nodeNew', 'nodeCopy', 'nodePaste', None, 'queryDeleteAll']
        vitables.utils.addActions(self.root_node_cm, actions, self.gui_actions)

        self.group_node_cm = QtWidgets.QMenu(self)
        self.group_node_cm.setObjectName('group_node_cm')
        actions = ['nodeProperties', None, 'nodeNew', 'nodeRename', 'nodeCut',
                   'nodeCopy', 'nodePaste', 'nodeDelete']
        vitables.utils.addActions(self.group_node_cm, actions,
                                  self.gui_actions)

        self.leaf_node_cm = QtWidgets.QMenu(self)
        self.leaf_node_cm.setObjectName('leaf_node_cm')
        actions = ['nodeOpen', 'nodeClose', None, 'nodeProperties', None,
                   'nodeRename', 'nodeCut', 'nodeCopy', 'nodePaste',
                   'nodeDelete', None, 'queryNew']
        vitables.utils.addActions(self.leaf_node_cm, actions, self.gui_actions)

        self.mdi_cm = QtWidgets.QMenu(self)
        self.mdi_cm.setObjectName('mdi_cm')
        actions = [self.window_menu]
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
        QtWidgets.qApp.quit()

    def makeCopy(self):
        """Copy text/leaf depending on which widget has focus.

        This method disambiguates the ``Ctrl+C`` shortcut. If the console has
        focus then ``Ctrl+C`` will copy the console selected text. If the
        databases tree view has focus then the selected node (if any) will be
        copied.
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
            action = QtWidgets.QAction('{0:>2} {1}.'.format(index, filepath),
                                       self,
                                       triggered=self.vtapp.openRecentFile)
            action.setData(item)
            if mode == 'r':
                action.setIcon(iconset['file_ro'])
            else:
                action.setIcon(iconset['file_rw'])
            self.open_recent_submenu.addAction(action)

        # Always add a separator and a clear QAction. So if the menu is empty
        # the user still will know what's going on
        self.open_recent_submenu.addSeparator()
        action = QtWidgets.QAction(
            translate('VTGUI', '&Clear', 'Recent File submenu entry'),
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

        # Clear the menu and rebuild it from scratch
        wmenu = self.window_menu
        wmenu.clear()
        window_actions = ['windowCascade', 'windowTile', 'windowRestoreAll',
                          'windowMinimizeAll', 'windowClose', 'windowCloseAll',
                          None, 'mdiTabbed', 'windowSeparator']
        vitables.utils.addActions(wmenu, window_actions, self.gui_actions)

        windows_list = self.workspace.subWindowList()
        if not windows_list:
            return

        # Create actions for the existing views
        action_group = QtWidgets.QActionGroup(wmenu)
        wmenu.action_group = action_group
        counter = 1
        for window in windows_list:
            title = window.windowTitle()
            if counter < 10:
                action = wmenu.addAction("&{0:d} {1}".format(counter, title))
                wmenu.action_group.addAction(action)
            elif counter == 10:
                wmenu.addSeparator()
                submenu = wmenu.addMenu(
                    translate('VTGUI', "&More...", 'A Windows submenu'))
                action_subgroup = QtWidgets.QActionGroup(submenu)
            elif counter < 36:
                atext = "&{0} {1}".format(chr(counter + ord("@") - 10), title)
                action = submenu.addAction(atext)
                action_subgroup.addAction(action)

            self.window_mapper.setMapping(action, window)
            action.triggered.connect(self.window_mapper.map)
            action.setCheckable(True)
            if self.workspace.activeSubWindow() == window:
                action.setChecked(True)
            counter = counter + 1

    def updateStatusBar(self):
        """Update the permanent message of the status bar.
        """

        current = self.dbs_tree_view.currentIndex()
        if current.isValid():
            tip = self.dbs_tree_model.data(current, QtCore.Qt.StatusTipRole)
            message = tip
        else:
            message = ''
        self.sb_node_info.setText(message)

    def popupContextMenu(self, kind, pos):
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

            - `nodepath`: the full path of the node that is overwrting other
                nodes
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

        if self.workspace.viewMode() == QtWidgets.QMdiArea.SubWindowView:
            self.workspace.setViewMode(QtWidgets.QMdiArea.TabbedView)
        else:
            self.workspace.setViewMode(QtWidgets.QMdiArea.SubWindowView)

    def eventFilter(self, widget, event):
        """Event filter used to provide the workspace with a context menu.

        :Parameters:

            - `widget`: the widget that receives the event
            - `event`: the event being processed
        """

        if widget == self.workspace:
            if event.type() == QtCore.QEvent.ContextMenu:
                # If active mdi subwindow can handle context menu
                # pass the event to it
                active_window = self.workspace.activeSubWindow()
                if active_window is not None and \
                        hasattr(active_window, 'is_context_menu_custom'):
                    is_cm_custom = active_window.is_context_menu_custom
                else:
                    is_cm_custom = False
                if not is_cm_custom:
                    pos = event.globalPos()
                    self.mdi_cm.popup(pos)
            return QtWidgets.QMdiArea.eventFilter(widget, widget, event)
        else:
            return QtWidgets.QMainWindow.eventFilter(self, widget, event)
