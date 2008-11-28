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
#       $Id: browserGUI.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the HelpBrowserGUI class and its helper classes.

Classes:

* HelpBrowserGUI(qt.QMainWindow) 

Methods:

* __init__(self, hb, docDir, iconsDir) 
* __tr(self, source, comment=None)
* closeEvent(self, event) 
* loadIcons(self) 
* initPopups(self) 
* initMenuBar(self)
* initToolbar(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os

import qt

from vitables.docBrowser import vtTextBrowser

class HelpBrowserGUI(qt.QMainWindow) :
    """Very simple documentation browser."""


    def __init__(self, hb, docDir, iconsDir) :
        """
        Initializes the browser.
        
        :Parameters:

        - `hb`: is an instance of `HelpBrowser`
        - `iconsDir`: the icons directory 
        - `docsDir`: the documentation directory 
        """

        qt.QMainWindow.__init__(self, None, 'HelpBrowserGUI instance')
        self.setWFlags(qt.Qt.WType_TopLevel|qt.Qt.WDestructiveClose)

        self.setCaption(self.__tr('Documentation browser', 'The window title'))
        self.resize(600, 600)

        self.helpBrowser = hb
        self.docDir = docDir
        self.iconsDir = iconsDir

        # The browser widget
        self.text_browser = vtTextBrowser.VTTextBrowser(self)
        self.text_browser.refreshSourceFactory(self.docDir)
        self.setCentralWidget(self.text_browser)

        # The popup menus
        self.actions = {}
        self.file_menu = qt.QPopupMenu()
        self.view_menu = qt.QPopupMenu()
        self.go_menu = qt.QPopupMenu()
        self.bookmarks_menu = qt.QPopupMenu()
        self.help_menu = qt.QPopupMenu()

        # The toolbar
        self.navigationBar = qt.QToolBar(self, 'navigation toolbar')

        self.iconsDictionary = self.loadIcons()
        self.initPopups()
        self.initMenuBar()
        self.initToolbar()
        self.statusBar().\
            message(self.__tr('Ready...', 'Status bar startup message'))


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('HelpBrowserGUI', source, comment).latin1()


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
        vtapp = self.helpBrowser.vtapp
        vtapp.docBrowsers.remove(self.helpBrowser)
        self.helpBrowser.slotCloseWindow()
        qt.QMainWindow.closeEvent(self, event)


    def loadIcons(self) :
        """
        Create toolbar and popup menus icons.

        This method convert png files from the specified directory to xpm
        format and then creates a `QIconSet` that will be used in the menubar
        and the toolbar. Original icons are taken from the `crystal SVG` set by
        everaldo.

        Note: the play_back icon has been made by myself with the `imagemagick`
        tool display.
        """

        large_icons = [
        # Icons for toolbar
        'gohome', 'player_back', 'player_play', 'reload_page',
        'bookmark', 'bookmark_add', 'viewmag+', 'viewmag-', 'history_clear']

        small_icons = [
        # Icons for menu items
        'fileopen', 'exit',
        'viewmag+', 'viewmag-',
        'gohome', 'player_back', 'player_play', 'reload_page',
        'bookmark', 'bookmark_add',
        # Icons for buttons
        'ok', 'cancel', 'remove']

        all_icons = [
        'fileopen', 'exit',
        'viewmag+', 'viewmag-',
        'gohome', 'player_back', 'player_play', 'reload_page',
        'bookmark', 'bookmark_add',
        'history_clear',
        'ok', 'cancel', 'remove']

        icons_dictionary = {} 
        for name in all_icons:
            iconset = qt.QIconSet()
            if name in large_icons:
                iconset.setIconSize(qt.QIconSet.Large, qt.QSize(22, 22))
                filename = 'big_icons/%s.png' % name
                filepath = os.path.join(self.iconsDir, filename)
                pixmap = qt.QPixmap()
                pixmap.load(filepath)
                iconset.setPixmap(pixmap, qt.QIconSet.Large, qt.QIconSet.Normal,
                    qt.QIconSet.On)
            if name in small_icons:
                filename = 'small_icons/%s.png' % name
                filepath = os.path.join(self.iconsDir, filename)
                pixmap = qt.QPixmap()
                pixmap.load(filepath)
                iconset.setPixmap(pixmap, qt.QIconSet.Small, qt.QIconSet.Normal,
                    qt.QIconSet.On)
            icons_dictionary[name] = iconset
        return icons_dictionary


    def initPopups(self) :
        """
        GUI components are: menu bar, tool bar and status bar.

        Menu bar menus: File, Go, Bookmarks, Help
        Tool bar buttons: home, backward, forward, combobox, clear history
        For every menu the `QMenuItems` are added from `QActions`, except for
        the Bookmarks menu, where we use also the `insertItem` method.

        The actions definitions are given in tuples with the structure
        ``(actionID, statusbarText, icon, menuText, accel, parent)``
        """

        #########################################################
        #
        # 					File menu
        #
        #########################################################

        # Icons 
        file_exit_icon = self.iconsDictionary['exit']
        file_open_icon = self.iconsDictionary['fileopen']

        # Actions
        file_menu_actions = [
            ('newBrowser', 
                self.__tr('New window', 
                    'Status bar text for the File --> New Window action'), 
                self.__tr('&New Window', 'File --> New Window'), 
                qt.QKeySequence('CTRL+N'), 
                self),

            ('openFile', 
                self.__tr('Open file', 
                    'Status bar text for the File --> Open File action'), 
                file_open_icon,
                self.__tr('&Open File', 'File --> Open File'), 
                qt.QKeySequence('CTRL+O'), 
                self),

            ('closeWindow', 
                self.__tr('Close window', 
                    'Status bar text for the File --> Close Window action'), 
                self.__tr('Close Window', 'File --> Close Window'), 
                qt.QKeySequence('CTRL+W'), 
                self),

            ('exitBrowser', 
                self.__tr('Close Help Browser', 
                    'Status bar text for the File --> Exit action'),
                file_exit_icon, 
                self.__tr('E&xit', 'File --> Exit'), 
                qt.QKeySequence('CTRL+Q'), 
                self)
        ]

        # Add items to menu
        for action_def in file_menu_actions :
            action_id = action_def[0]
            self.actions[action_id] = apply(qt.QAction, action_def[2:])
            self.actions[action_id].setStatusTip(action_def[1])
            self.actions[action_id].addTo(self.file_menu)
        self.file_menu.insertSeparator(3)

        #########################################################
        #
        # 					View menu
        #
        #########################################################

        # Icons 
        view_zoom_in_icon = self.iconsDictionary['viewmag+']
        view_zoom_out_icon = self.iconsDictionary['viewmag-']

        # Actions
        view_menu_actions = [
            ('zoomIn', 
                self.__tr('Increases the font size', 
                    'Status bar text for the View --> Zoom in action'),
                view_zoom_in_icon,
                self.__tr('Zoom &in', 'View --> Zoom in'), 
                qt.QKeySequence('CTRL++'), 
                self),

            ('zoomOut', 
                self.__tr('Decreases the font size', 
                    'Status bar text for the View --> Zoom out action'),
                view_zoom_out_icon,
                self.__tr('Zoom &out', 'View --> Zoom out'), 
                qt.QKeySequence('CTRL+-'), 
                self)
        ]

        # Add items to menu
        for action_def in view_menu_actions :
            action_id = action_def[0]
            self.actions[action_id] = apply(qt.QAction, action_def[2:])
            self.actions[action_id].setStatusTip(action_def[1])
            self.actions[action_id].addTo(self.view_menu)

        #########################################################
        #
        # 					Go menu
        #
        #########################################################
 
        # Icons 
        go_home_icon = self.iconsDictionary['gohome']
        go_backward_icon = self.iconsDictionary['player_back']
        go_forward_icon = self.iconsDictionary['player_play']
        go_reload_icon = self.iconsDictionary['reload_page']

        # Actions
        go_menu_actions = [
            ('goHome', 
                self.__tr('Go to the first visited page', 
                    'Status bar text for the  Go --> Home action'), 
                go_home_icon, 
                self.__tr('&Home', 'Go --> Home'), 
                qt.QKeySequence(), 
                self), 
            ('goBackward', 
                self.__tr('Go to previous page', 
                    'Status bar text for the  Go --> Backward action'),
                go_backward_icon, 
                self.__tr('&Backward', ' Go --> Backward'), 
                qt.QKeySequence('CTRL+Left'),
                self), 
            ('goForward', 
                self.__tr('Go to next page', 
                    'Status bar text for the  Go --> Forward action'), 
                go_forward_icon, 
                self.__tr('&Forward', 'HelpBrowser'), 
                qt.QKeySequence('CTRL+Right'), 
                self),
            ('goReload', 
                self.__tr('Reload the current page', 
                    'Status bar text for the  Go --> Reload action'), 
                go_reload_icon, 
                self.__tr('&Reload', 'Go --> Reload'), 
                qt.QKeySequence(''), 
                self)
        ]

        # Adds items to menu
        for action_def in go_menu_actions :
            action_id = action_def[0]
            self.actions[action_id] = apply(qt.QAction, action_def[2:])
            self.actions[action_id].setStatusTip(action_def[1])
            self.actions[action_id].addTo(self.go_menu)

        #########################################################
        #
        # 					Bookmarks menu
        #
        #########################################################

        # This menu is a special case. It is due to its dynamic nature.
        # The menu content may vary every time a bookmark is added/deleted
        # In order to track changes and keep it updated, the menu it is reloaded
        # every time it is about to be displayed. This goal is achieved using
        # signal/slot mechanism (see code below). 

        # Icons
        bookmarks_edit_icon = self.iconsDictionary['bookmark']
        bookmarks_add_icon = self.iconsDictionary['bookmark_add']
        # Actions
        self.bookmarks_menu_actions = [
            ('bookmarksAdd', 
                self.__tr('Bookmark the current page', 
                    'Status bar text for Bookmarks --> Add bookmark action'), 
                bookmarks_add_icon, 
                self.__tr('&Add bookmark', 'Bookmarks --> Add bookmark'), 
                qt.QKeySequence('CTRL+Alt+N'), 
                self),
            ('bookmarksEdit', 
                self.__tr('Edit bookmarks', 
                    'Status bar text for Bookmarks --> Edit bookmarks action'),
                bookmarks_edit_icon, 
                self.__tr('&Edit bookmarks...', 'Bookmarks --> Edit bookmarks'), 
                qt.QKeySequence('CTRL+Alt+E'), 
                self),
            ('bookmarksClear', 
                self.__tr('Clear all existing bookmarks', 
                    'Status bar text for Bookmarks --> Add bookmark action'), 
                self.__tr('&Clear All', 'Bookmarks --> Add bookmark'), 
                qt.QKeySequence('CTRL+Alt+C'), 
                self)
        ]

        # Adds items to menu
        for action_def in self.bookmarks_menu_actions :
            action_id = action_def[0]
            self.actions[action_id] = apply(qt.QAction, action_def[2:])
            self.actions[action_id].setStatusTip(action_def[1])
            self.actions[action_id].addTo(self.bookmarks_menu)
        self.bookmarks_menu.setId(0, 1000)
        self.bookmarks_menu.setId(1, 2000)
        self.bookmarks_menu.setId(1, 3000)
        self.bookmarks_menu.insertSeparator()

        #########################################################
        #
        # 					Help menu
        #
        #########################################################

        # Actions
        help_menu_actions = [
            ('about', 
                self.__tr('About HelpBrowser', 
                    'Status bar text for Help --> About HelpBrowser action'), 
                self.__tr('&About HelpBrowser', 'Help --> About HelpBrowser'), 
                qt.QKeySequence(), 
                self),
            ('aboutQt', 
                self.__tr('About Qt', 
                    'Status bar text for the Help --> About Qt action'), 
                self.__tr('About &Qt', 'Help --> About Qt'), 
                qt.QKeySequence(), 
                self)
        ]

        # Adds actions to menu
        for action_def in help_menu_actions :
            action_id = action_def[0]
            self.actions[action_id] = apply(qt.QAction, action_def[2:])
            self.actions[action_id].setStatusTip(action_def[1])
            self.actions[action_id].addTo(self.help_menu)

    def initMenuBar(self):
        """
        Init the menu bar.

        Make popup menus and add them to the menu bar.
        """

        # popups are added to the menu bar
        menubar_items = [
            (self.__tr('&File', 'The File menu title'), self.file_menu),
            (self.__tr('&View', 'The View menu title'), self.view_menu),
            (self.__tr('&Go', 'The Go menu title'), self.go_menu),
            (self.__tr('&Bookmarks', 'The Bookmarks menu title'),
                self.bookmarks_menu),
            (self.__tr('&Help', 'The Help menu title'), self.help_menu)
        ]
        for (label, item) in menubar_items:
            self.menuBar().insertItem(label, item)


    def initToolbar(self):
        """
        Initializes toolbar.

        The toolbar is made of several toolbars.
        Individual toolbars are made of a subset of actions of the
        corresponding popup menu.
        All toolbar buttons have been resized to make them more visible.
        """

        # The toolbar will have buttons, labels and a combobox
        # If the HelpBrowser resizes we want the combobox to resize too,
        # but all other widgets must keep its original size. This can be
        # achieved if: 
        # 1) the toolbar is stretchable
        # 2) the combobox is stretchable
        # 3) we set the buttons and labels size policy to Fixed/Minimum

        self.navigationBar.setHorizontallyStretchable(1)
        
        # Icons
        nav_delete_icon = self.iconsDictionary['history_clear']
        
        # Actions
        self.actions['clearSession'] = \
            qt.QAction(self.__tr('Clear the list of visited pages', 
                    'Status bar text for the Clear Session toolbar action'),
                nav_delete_icon, 
                self.__tr('Clear session', 
                    'Tooltip for the Clear Session toolbar action'), 
                qt.QKeySequence(), 
                self)
        
        # Adds items to the toolbar: actions, separators and stuff like that
        toolbar_action_ids = ['goHome', 'goBackward', 'goForward', 'goReload', 
            'separator', 'bookmarksAdd', 'bookmarksEdit', 'separator',\
            'zoomIn', 'zoomOut']
        for action_id in toolbar_action_ids :
            if action_id == 'separator' :
                self.navigationBar.addSeparator()
            else :
                self.actions[action_id].addTo(self.navigationBar)

        self.navigationBar.addSeparator()

        self.actions['clearSession'].addTo(self.navigationBar)

        goSelector = \
            qt.QLabel(self.__tr('Go: ', 'Text of the Go: label'), 
                self.navigationBar)
        self.comboHistory = qt.QComboBox(self.navigationBar)

        # Set the size of toolbuttons icons to 22x22 (see loadIcons method)
        children = self.navigationBar.children()
        tool_buttons = \
            [child for child in children if isinstance(child, qt.QToolButton)]
        for tbutton in tool_buttons :
            tbutton.setUsesBigPixmap(1)
        
        # Set the size policy for buttons and labels
        children_list = self.navigationBar.children()
        for child in children_list :
            if isinstance(child, qt.QToolButton) or \
                isinstance(child, qt.QLabel) :
                child.setSizePolicy(qt.QSizePolicy.Fixed, \
                qt.QSizePolicy.Minimum)
        
        # Setup combobox
        self.navigationBar.setStretchableWidget(self.comboHistory)
        self.comboHistory.setEditable(0)
        qt.QWhatsThis.add(self.comboHistory, self.__tr(
            """<qt>
            <h3>Page selector</h3>Select the page you want to visit.
            </qt>""", 
            'WhatsThis text for the combobox of visited pages')
            )
        for item in self.helpBrowser.history :
            self.comboHistory.insertItem(item)

