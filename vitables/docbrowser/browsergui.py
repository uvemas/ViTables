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
Here is defined the HelpBrowserGUI class.

This module creates the main window for the documentation browser.
"""

__docformat__ = 'restructuredtext'

import re

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils
from vitables.vtsite import DOCDIR


translate = QtWidgets.QApplication.translate


class HelpBrowserGUI(QtWidgets.QMainWindow) :
    """
    The main window of the documentation browser.

    :Parameters:

    - `browser`: an instance of the docs browser controller
      :meth:`vitables.docbrowser.helpbrowser.HelpBrowser`
    - `parent`: the parent widget.
    """

    def __init__(self, browser, parent=None) :
        """
        Initializes the browser.
        """

        super(HelpBrowserGUI, self).__init__(parent)

        self.setIconSize(QtCore.QSize(22, 22))
        self.setWindowTitle(translate('HelpBrowserGUI',
            'Documentation browser', 'The window title'))
        self.icons = vitables.utils.getHBIcons()
        self.setWindowIcon(self.icons['vitables_wm'])

        self.browser = browser

        # The browser widget
        self.text_browser = QtWidgets.QTextBrowser()
        self.text_browser.setSearchPaths([DOCDIR])
        self.setCentralWidget(self.text_browser)
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setReadOnly(1)

        # The popup menus
        self.actions = self.setupActions()
        self.initPopups()
        self.connectSignals()
        self.setupHistoryCombo()
        self.statusBar().showMessage(translate('HelpBrowserGUI', 'Ready...',
                                    'Status bar startup message'))


    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        actions = {}

        actions['exitBrowser'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', 'E&xit', 'File --> Exit'), self,
            shortcut=QtGui.QKeySequence.Quit,
            triggered=self.browser.exitBrowser,
            icon=self.icons['application-exit'],
            statusTip=translate('HelpBrowserGUI', 'Close Help Browser',
                    'Status bar text for the File --> Exit action'))

        actions['zoomIn'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', 'Zoom &in', 'View --> Zoom in'), self,
            shortcut=QtGui.QKeySequence.ZoomIn,
            triggered=self.browser.zoomIn,
            icon=self.icons['zoom-in'],
            statusTip=translate('HelpBrowserGUI', 'Increases the font size',
                'Status bar text for the View --> Zoom in action'))

        actions['zoomOut'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', 'Zoom &out', 'View --> Zoom out'),
            self,
            shortcut=QtGui.QKeySequence.ZoomOut,
            triggered=self.browser.zoomOut,
            icon=self.icons['zoom-out'],
            statusTip=translate('HelpBrowserGUI', 'Decreases the font size',
                'Status bar text for the View --> Zoom out action'))

        actions['goHome'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Home', 'Go --> Home'), self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.text_browser.home,
            icon=self.icons['go-first-view'],
            statusTip=translate('HelpBrowserGUI',
                'Go to the first visited page',
                'Status bar text for the  Go --> Home action'))

        actions['goBackward'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Backward', ' Go --> Backward'),
            self,
            shortcut=QtGui.QKeySequence.Back,
            triggered=self.text_browser.backward,
            icon=self.icons['go-previous-view'],
            statusTip=translate('HelpBrowserGUI', 'Go to previous page',
                'Status bar text for the  Go --> Backward action'))

        actions['goForward'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Forward', ' Go --> Forward'), self,
            shortcut=QtGui.QKeySequence.Forward,
            triggered=self.text_browser.forward,
            icon=self.icons['go-next-view'],
            statusTip=translate('HelpBrowserGUI', 'Go to next page',
                'Status bar text for the  Go --> Forward action'))

        actions['goReload'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Reload', 'Go --> Reload'), self,
            shortcut=QtGui.QKeySequence.Refresh,
            triggered=self.text_browser.reload,
            icon=self.icons['view-refresh'],
            statusTip=translate('HelpBrowserGUI', 'Reload the current page',
                'Status bar text for the  Go --> Reload action'))

        actions['bookmarksAdd'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Add bookmark',
                'Bookmarks --> Add bookmark'),
            self,
            shortcut=QtGui.QKeySequence('Ctrl+Alt+N'),
            triggered=self.browser.addBookmark,
            icon=self.icons['bookmark_add'],
            statusTip=translate('HelpBrowserGUI', 'Bookmark the current page',
                'Status bar text for Bookmarks --> Add bookmark action'))

        actions['bookmarksEdit'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Edit bookmarks...',
                'Bookmarks --> Edit bookmarks'),
            self,
            shortcut=QtGui.QKeySequence('Ctrl+Alt+E'),
            triggered=self.browser.editBookmarks,
            icon=self.icons['bookmarks'],
            statusTip=translate('HelpBrowserGUI', 'Edit bookmarks',
                'Status bar text for Bookmarks --> Edit bookmarks action'))

        actions['bookmarksClear'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&Clear All',
                'Bookmarks --> Clear bookmark'),
            self,
            shortcut=QtGui.QKeySequence('Ctrl+Alt+C'),
            triggered=self.browser.clearBookmarks,
            statusTip=translate('HelpBrowserGUI',
                'Clear all existing bookmarks',
                'Status bar text for Bookmarks --> Add bookmark action'))

        actions['about'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', '&About HelpBrowser',
                'Help --> About HelpBrowser'),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.browser.aboutBrowser,
            statusTip=translate('HelpBrowserGUI', 'About HelpBrowser',
                'Status bar text for Help --> About HelpBrowser action'))

        actions['aboutQt'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', 'About &Qt', 'Help --> About Qt'),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.browser.aboutQt,
            statusTip=translate('HelpBrowserGUI', 'About Qt',
                'Status bar text for the Help --> About Qt action'))

        actions['clearSession'] = QtWidgets.QAction(
            translate('HelpBrowserGUI', 'Clear history', ''), self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.browser.clearHistory,
            icon=self.icons['edit-clear-history'],
            statusTip=translate('HelpBrowserGUI',
                'Clear the content of the history combobox', ''))

        return actions


    def initPopups(self) :
        """
        Setup the menubar and the toolbar of the main window.

        The menubar contains the menus `File`, `Go`, `Bookmarks` and `Help`.
        The toolbar contains the buttons: `home`, `backward`, `forward`,
        `combobox` and `clear history`.
        """

        # Create the File menu and add actions/submenus/separators to it
        file_menu = self.menuBar().addMenu(
            translate('HelpBrowserGUI', "&File", 'The File menu entry'))
        file_actions = ['exitBrowser']
        vitables.utils.addActions(file_menu, file_actions, self.actions)


        # Create the View menu and toolbar
        view_menu = self.menuBar().addMenu(
            translate('HelpBrowserGUI', "&View", 'The View menu entry'))
        view_toolbar = QtWidgets.QToolBar(
            translate('HelpBrowserGUI', 'View operations', 'Toolbar title'),
            self)
        self.addToolBar(view_toolbar)
        view_actions = ['zoomIn', 'zoomOut']
        vitables.utils.addActions(view_menu, view_actions, self.actions)
        vitables.utils.addActions(view_toolbar, view_actions, self.actions)

        # Create the Go menu and toolbar
        go_menu = self.menuBar().addMenu(translate('HelpBrowserGUI', "&Go",
            'The Go menu entry'))
        go_toolbar = QtWidgets.QToolBar(
            translate('HelpBrowserGUI', 'Go operations', 'Toolbar title'),
            self)
        self.addToolBar(go_toolbar)
        go_actions = ['goHome', 'goBackward', 'goForward', 'goReload']
        vitables.utils.addActions(go_menu, go_actions, self.actions)
        vitables.utils.addActions(go_toolbar, go_actions, self.actions)


        # Create the Bookmarks menu and toolbar
        self.bookmarks_menu = self.menuBar().addMenu(
            translate('HelpBrowserGUI', "&Bookmarks", 'Bookmarks menu entry'))
        bookmarks_toolbar = QtWidgets.QToolBar(
            translate('HelpBrowserGUI', 'Bookmarks operations',
            'Toolbar title'), self)
        self.addToolBar(bookmarks_toolbar)
        bookmark_actions = ['bookmarksAdd', 'bookmarksEdit', 'bookmarksClear',
                            None]
        vitables.utils.addActions(self.bookmarks_menu, bookmark_actions,
            self.actions)
        vitables.utils.addActions(bookmarks_toolbar, bookmark_actions[:2],
            self.actions)

        # Create the Help menu and add actions/submenus/separators to it
        help_menu = self.menuBar().addMenu(
            translate('HelpBrowserGUI', "&Help", 'The Help menu entry'))
        help_actions = ['about', 'aboutQt']
        vitables.utils.addActions(help_menu, help_actions, self.actions)

        # Create the History toolbar
        history_toolbar = QtWidgets.QToolBar(
            translate('HelpBrowserGUI', 'History operations', 'Toolbar title'),
            self)
        self.addToolBar(history_toolbar)
        history_actions = ['clearSession']
        vitables.utils.addActions(history_toolbar, history_actions,
            self.actions)
        go_selector = QtWidgets.QLabel(
            translate('HelpBrowserGUI', 'Go: ', 'Text of the Go: label'),
            history_toolbar)
        history_toolbar.addWidget(go_selector)
        self.combo_history = QtWidgets.QComboBox(history_toolbar)
        self.combo_history.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToContents)
        history_toolbar.addWidget(self.combo_history)


    def connectSignals(self):
        """
        Connect signals to slots.

        Signals coming from GUI are connected to slots in the docs browser
        controller, :meth:`vitables.docbrowser.helpbrowser.HelpBrowser`.
        """

        self.combo_history.activated[str].connect(self.browser.displaySrc)

        # This is the most subtle connection. It encompasses source
        # changes coming from anywhere, including slots (home, backward
        # and forward), menus (Go and Bookmarks), clicked links and
        # programatic changes (setSource calls).
        self.text_browser.sourceChanged.connect(self.browser.updateHistory)

        self.text_browser.backwardAvailable.connect(
            self.browser.updateBackward)

        self.text_browser.forwardAvailable.connect(
            self.browser.updateForward)

        # The Bookmarks menu is special case due to its dynamic nature.
        # The menu content vary every time a bookmark is added/deleted
        # In order to track changes and keep it updated, the menu is reloaded
        # every time it is about to be displayed.
        self.bookmarks_menu.aboutToShow.connect(self.updateRecentSubmenu)


    def updateRecentSubmenu(self):
        """Update the content of the Bookmarks menu."""

        # Clear the current bookmarks from the Bookmarks menu
        for action in self.bookmarks_menu.actions():
            if re.search("^(\s?\d)", action.text()):
                self.bookmarks_menu.removeAction(action)
        # and refresh it
        index = 0
        for filepath in self.browser.bookmarks:
            index += 1
            action = QtWidgets.QAction('{0:>2}. {1}'.format(index, filepath),
                                    self.bookmarks_menu)
            action.setData(filepath)
            self.bookmarks_menu.addAction(action)
            action.triggered.connect(self.browser.displaySrc)


    def setupHistoryCombo(self):
        """
        Initializes history combobox.
        """

        # Setup combobox
        self.combo_history.setEditable(0)
        self.combo_history.setWhatsThis(translate('HelpBrowserGUI',
            """<qt>
            <h3>Page selector</h3>Select the page you want to visit.
            </qt>""",
            'WhatsThis text for the combobox of visited pages')
            )
        for item in self.browser.history :
            self.combo_history.addItem(item)


    def closeEvent(self, event) :
        """
        Reimplements the event handler for `QCloseEvent` events.

        Before the close event is accepted we need to do some stuff. This can
        be done in two different ways: via event filters or reimplementing the
        event handler. We have chosen the second possibility.

        :Parameter event: the event being handled
        """

        # When the help browser window is closed via File --> Exit
        # the exitBrowser is called and its history is saved.
        # But if we close the window with the
        # close button then history is not saved at all.
        # We fix this misbehavior by overwriting this method.
        self.browser.exitBrowser()
        QtWidgets.QMainWindow.closeEvent(self, event)
