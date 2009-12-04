# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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

Classes:

* HelpBrowserGUI(QMainWindow) 

Methods:

* __init__(self, browser, parent=None) 
* setupActions(self)
* initPopups(self) 
* setupHistoryCombo(self)
* connectSignals(self)
* closeEvent(self, event) 

Functions:

* trs(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'HeHelpBrowserGUI'

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import DOCDIR



def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))
class HelpBrowserGUI(QtGui.QMainWindow) :
    """Very simple documentation browser."""

    def __init__(self, browser, parent=None) :
        """
        Initializes the browser.

        :Parameters:

        - `browser`: is an instance of `HelpBrowser`
        - `parent`: the parent widget.
        """

        QtGui.QMainWindow.__init__(self, parent)

        self.setIconSize(QtCore.QSize(22, 22))
        self.setWindowTitle(trs('Documentation browser', 
            'The window title'))
        self.icons = vitables.utils.getHBIcons()
        self.setWindowIcon(self.icons['vitables_wm'])

        self.browser = browser

        # The browser widget
        self.text_browser = QtGui.QTextBrowser()
        self.text_browser.setSearchPaths(QtCore.QStringList(DOCDIR))
        self.setCentralWidget(self.text_browser)
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setReadOnly(1)

        # The popup menus
        self.actions = self.setupActions()
        self.initPopups()
        self.connectSignals()
        self.setupHistoryCombo()
        self.statusBar().showMessage(trs('Ready...', 
                                    'Status bar startup message'))


    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        actions = {}
        actions['newBrowser'] = vitables.utils.createAction(self, 
                trs('&New Window', 'File --> New Window'), 
                QtGui.QKeySequence.New, self.browser.slotNewBrowser, 
                None, 
                trs('New window', 
                    'Status bar text for the File --> New Window action'))

        actions['openFile'] = vitables.utils.createAction(self, 
                trs('&Open File', 'File --> Open File'), 
                QtGui.QKeySequence.Open, self.browser.slotOpenFile, 
                self.icons['document-open'], 
                trs('Open file', 
                    'Status bar text for the File --> Open File action'))

        actions['closeWindow'] = vitables.utils.createAction(self, 
                trs('Close Window', 'File --> Close Window'), 
                QtGui.QKeySequence.Close, self.browser.slotCloseWindow, 
                None, 
                trs('Close window', 
                    'Status bar text for the File --> Close Window action'))

        actions['exitBrowser'] = vitables.utils.createAction(self, 
                trs('E&xit', 'File --> Exit'), 
                QtGui.QKeySequence('CTRL+Q'), self.browser.slotExitBrowser, 
                self.icons['application-exit'], 
                trs('Close Help Browser', 
                    'Status bar text for the File --> Exit action'))

        actions['zoomIn'] = vitables.utils.createAction(self, 
                trs('Zoom &in', 'View --> Zoom in'), 
                QtGui.QKeySequence.ZoomIn, self.browser.slotZoomIn, 
                self.icons['zoom-in'], 
                trs('Increases the font size', 
                    'Status bar text for the View --> Zoom in action'))

        actions['zoomOut'] = vitables.utils.createAction(self, 
                trs('Zoom &out', 'View --> Zoom out'), 
                QtGui.QKeySequence.ZoomOut, self.browser.slotZoomOut, 
                self.icons['zoom-out'], 
                trs('Decreases the font size', 
                    'Status bar text for the View --> Zoom out action'))

        actions['goHome'] = vitables.utils.createAction(self.text_browser, 
                trs('&Home', 'Go --> Home'), 
                QtGui.QKeySequence.UnknownKey, QtCore.SLOT('home()'), 
                self.icons['go-first-view'], 
                trs('Go to the first visited page', 
                    'Status bar text for the  Go --> Home action'))

        actions['goBackward'] = vitables.utils.createAction(self.text_browser, 
                trs('&Backward', ' Go --> Backward'), 
                QtGui.QKeySequence.Back, QtCore.SLOT('backward()'), 
                self.icons['go-previous-view'], 
                trs('Go to previous page', 
                    'Status bar text for the  Go --> Backward action'))

        actions['goForward'] = vitables.utils.createAction(self.text_browser, 
                trs('&Forward', ' Go --> Forward'), 
                QtGui.QKeySequence.Forward, QtCore.SLOT('forward()'), 
                self.icons['go-next-view'], 
                trs('Go to next page', 
                    'Status bar text for the  Go --> Forward action'))

        actions['goReload'] = vitables.utils.createAction(self.text_browser, 
                trs('&Reload', 'Go --> Reload'), 
                QtGui.QKeySequence.Refresh, QtCore.SLOT('reload()'), 
                self.icons['view-refresh'], 
                trs('Reload the current page', 
                    'Status bar text for the  Go --> Reload action'))

        actions['bookmarksAdd'] = vitables.utils.createAction(self, 
                trs('&Add bookmark', 'Bookmarks --> Add bookmark'), 
                QtGui.QKeySequence('CTRL+Alt+N'), 
                self.browser.slotAddBookmark, self.icons['bookmark_add'], 
                trs('Bookmark the current page', 
                    'Status bar text for Bookmarks --> Add bookmark action'))

        actions['bookmarksEdit'] = vitables.utils.createAction(self, 
                trs('&Edit bookmarks...', 
                          'Bookmarks --> Edit bookmarks'), 
                QtGui.QKeySequence('CTRL+Alt+E'), 
                self.browser.slotEditBookmarks, self.icons['bookmarks'], 
                trs('Edit bookmarks', 
                    'Status bar text for Bookmarks --> Edit bookmarks action'))

        actions['bookmarksClear'] = vitables.utils.createAction(self, 
                trs('&Clear All', 'Bookmarks --> Clear bookmark'), 
                QtGui.QKeySequence('CTRL+Alt+C'), 
                self.browser.slotClearBookmarks, None, 
                trs('Clear all existing bookmarks', 
                    'Status bar text for Bookmarks --> Add bookmark action'))

        actions['about'] = vitables.utils.createAction(self, 
                trs('&About HelpBrowser', 'Help --> About HelpBrowser'), 
                QtGui.QKeySequence.UnknownKey, 
                self.browser.slotAboutHelpBrowser, None, 
                trs('About HelpBrowser', 
                    'Status bar text for Help --> About HelpBrowser action'))

        actions['aboutQt'] = vitables.utils.createAction(self, 
                trs('About &Qt', 'Help --> About Qt'), 
                QtGui.QKeySequence.UnknownKey, self.browser.slotAboutQt, 
                None, 
                trs('About Qt', 
                    'Status bar text for the Help --> About Qt action'))

        actions['clearSession'] = vitables.utils.createAction(self, 
                trs('Clear history', ''), 
                QtGui.QKeySequence.UnknownKey, self.browser.slotClearHistory, 
                self.icons['edit-clear-history'], 
                trs('Clear the content of the history combobox', 
                    ''))
        return actions


    def initPopups(self) :
        """
        GUI components are: menu bar, tool bar and status bar.

        Menu bar menus: File, Go, Bookmarks, Help
        Tool bar buttons: home, backward, forward, combobox, clear history
        For every menu the `QMenuItems` are added from `QActions`, except for
        the Bookmarks menu, where we use also the `insertItem` method.
        """

        # Create the File menu and add actions/submenus/separators to it
        file_menu = self.menuBar().addMenu(trs("&File", 
            'The File menu entry'))
        file_actions = ['openFile', None, 'newBrowser', 'closeWindow', None, 
                        'exitBrowser']
        vitables.utils.addActions(file_menu, file_actions, self.actions)


        # Create the View menu and toolbar
        view_menu = self.menuBar().addMenu(trs("&View", 
            'The View menu entry'))
        view_toolbar = QtGui.QToolBar(trs('View operations', 
            'Toolbar title'), self)
        self.addToolBar(view_toolbar)
        view_actions = ['zoomIn', 'zoomOut']
        vitables.utils.addActions(view_menu, view_actions, self.actions)
        vitables.utils.addActions(view_toolbar, view_actions, self.actions)

        # Create the Go menu and toolbar
        go_menu = self.menuBar().addMenu(trs("&Go", 
            'The Go menu entry'))
        go_toolbar = QtGui.QToolBar(trs('Go operations', 
            'Toolbar title'), self)
        self.addToolBar(go_toolbar)
        go_actions = ['goHome', 'goBackward', 'goForward', 'goReload']
        vitables.utils.addActions(go_menu, go_actions, self.actions)
        vitables.utils.addActions(go_toolbar, go_actions, self.actions)


        # Create the Bookmarks menu and toolbar
        # This menu is a special case. It is due to its dynamic nature.
        # The menu content vary every time a bookmark is added/deleted
        # In order to track changes and keep it updated, the menu is reloaded
        # every time it is about to be displayed. This goal is achieved using
        # signal/slot mechanism (see helpBrowser.py module). 
        self.bookmarks_menu = self.menuBar().addMenu(trs("&Bookmarks", 
            'The Bookmarks menu entry'))
        bookmarks_toolbar = QtGui.QToolBar(trs('Bookmarks operations', 
            'Toolbar title'), self)
        self.addToolBar(bookmarks_toolbar)
        bookmark_actions = ['bookmarksAdd', 'bookmarksEdit', 'bookmarksClear', 
                            None]
        vitables.utils.addActions(self.bookmarks_menu, bookmark_actions, 
            self.actions)
        vitables.utils.addActions(bookmarks_toolbar, bookmark_actions[:2], 
            self.actions)

        # Create the Help menu and add actions/submenus/separators to it
        help_menu = self.menuBar().addMenu(trs("&Help", 
            'The Help menu entry'))
        help_actions = ['about', 'aboutQt']
        vitables.utils.addActions(help_menu, help_actions, self.actions)

        # Create the History toolbar
        history_toolbar = QtGui.QToolBar(trs('History operations', 
            'Toolbar title'), self)
        self.addToolBar(history_toolbar)
        history_actions = ['clearSession']
        vitables.utils.addActions(history_toolbar, history_actions, 
            self.actions)
        go_selector = \
            QtGui.QLabel(trs('Go: ', 'Text of the Go: label'), 
                history_toolbar)
        history_toolbar.addWidget(go_selector)
        self.combo_history = QtGui.QComboBox(history_toolbar)
        self.combo_history.setSizeAdjustPolicy(\
            QtGui.QComboBox.AdjustToContents)
        history_toolbar.addWidget(self.combo_history)


    def connectSignals(self):
        """
        Connect signals to slots.

        Signals coming from GUI are connected to slots in the docs 
        browser controller (`HelpBrowser`).
        """

        self.connect(self.combo_history, 
            QtCore.SIGNAL('activated(QString)'), self.browser.slotDisplaySrc)

        # This is the most subtle connection. It encompasses source
        # changes coming from anywhere, including slots (home, backward
        # and forward), menus (Go and Bookmarks), clicked links and
        # programatic changes (setSource calls).
        self.connect(self.text_browser, 
            QtCore.SIGNAL('sourceChanged(QUrl)'), 
            self.browser.updateHistory)

        self.connect(self.text_browser, 
            QtCore.SIGNAL('backwardAvailable(bool)'), 
            self.browser.slotUpdateBackward)

        self.connect(self.text_browser, 
            QtCore.SIGNAL('forwardAvailable(bool)'), 
            self.browser.slotUpdateForward)

        self.connect(self.bookmarks_menu, 
            QtCore.SIGNAL('aboutToShow()'), 
            self.browser.slotRecentSubmenuAboutToShow)


    def setupHistoryCombo(self):
        """
        Initializes history combobox.
        """

        # Setup combobox
        self.combo_history.setEditable(0)
        self.combo_history.setWhatsThis(trs(
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

        # When a help browser window is closed via File --> Close or via
        # File --> Exit the slotCloseWindow is called and its history is
        # saved (histories are not synchronised so only the last closed
        # window history is kept). But if we close the window with the
        # close button then history is not saved at all.
        # We fix this misbehavior by overwriting this method.
        vtapp = self.browser.vtapp
        vtapp.doc_browsers.remove(self.browser)
        self.browser.slotCloseWindow()
        QtGui.QMainWindow.closeEvent(self, event)
