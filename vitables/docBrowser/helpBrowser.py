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
Here is defined the HelpBrowser class.

Classes:

* HelpBrowser(QtCore.QObject) 

Methods:

* __init__(self, vtapp) 
* displaySrc(self, src=None)
* slotNewBrowser(self)
* slotOpenFile(self, filepath=None)
* slotCloseWindow(self)
* exitBrowser(self)
* zoomIn(self) 
* zoomOut(self) 
* updateHome(self) 
* updateForward(self, available)
* updateBackward(self, available)
* slotRecentSubmenuAboutToShow(self)
* slotOpenBookmark(self, bmark_id)
* addBookmark(self)
* editBookmarks(self)
* clearBookmarks(self)
* clearHistory(self)
* updateHistory(self, src) 
* aboutBrowser(self)
* aboutQt(self)

Functions:

* trs(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'HelpBrowser'

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.docBrowser import bookmarksDlg
from vitables.docBrowser import browserGUI


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class HelpBrowser(QtCore.QObject) :
    """
    Very simple documentation browser.

    ViTables uses this class to navigate help docs.
    Features:

    * reasonably good understanding of ``HTML`` format
    * navigation toolbar
    * session capable
      - filenames of files opened during the session are available at
          any moment
      - last session can be restored next time we open the `HelpBrowser`
    * basic bookmarks management
    """

    def __init__(self) :
        """
        Initializes the browser.

        Restore history and bookmarks from disk and makes the browser window.
        """

        QtCore.QObject.__init__(self)

        self.vtapp = vitables.utils.getVTApp()

        # Get the bookmarks and the navigation history
        self.bookmarks = self.vtapp.config.hb_bookmarks
        self.history = self.vtapp.config.hb_history

        # create the GUI
        self.gui = browserGUI.HelpBrowserGUI(self)

        # The working directory used in QFileDialog calls
        self.working_dir = vitables.utils.getHomeDir()

        # The GUI setup is slow so it is not shown until the setup is
        # done (it avoids displaying an ugly empty widget)
        self.displaySrc('index.html')
        self.gui.show()


    def displaySrc(self, src=False):
        """
        Displays a document in the `HelpBrowser` window.

        This slot is called when:

            - HelpBrowser.slotOpenFile is launched
            - BookmarksDlg.slotDisplayBookmark is launched
            - a new item is activated in the History combo
            - an entry is selected in the Bookmarks menu

        :Parameter src: the path of the file being displayed
        """

        if src is False: # entry selected in the Bookmarks menu
            action = self.gui.sender()
            src = action.data().toString()

        src = QtCore.QDir(src).dirName()
        src = QtCore.QDir().fromNativeSeparators(src) # src can be a QString
        url = QtCore.QUrl(src)
        self.gui.text_browser.setSource(url)

    #########################################################
    #
    # 					File menu related slots
    #
    #########################################################

    def exitBrowser(self) :
        """
        Quit the HelpBrowser.

        File --> Exit

        Before quitting this slot saves session and bookmarks. Then all browser
        windows are closed. The saved state corresponds to the window on which 
        Exit is invoqued.
        """

        # Close all browsers
        self.vtapp.config.hb_history = self.history
        self.vtapp.config.hb_bookmarks = self.bookmarks
        self.vtapp.doc_browser = None
        self.gui.close()

    #########################################################
    #
    # 					View menu related slots
    #
    #########################################################

    def zoomIn(self) :
        """Increases the font size of the displayed source."""
        self.gui.text_browser.zoomIn(2)


    def zoomOut(self) :
        """Increases the font size of the displayed source."""
        self.gui.text_browser.zoomOut(2)

    #########################################################
    #
    # 					Go menu related slots
    #
    #########################################################

    def updateHome(self) :
        """
        Enables/disables the Go --> Home menu item.

        If the history list is empty the menu item is disabled. Otherwise
        it is enabled.
        """

        if self.gui.text_browser.source():
            self.gui.actions['goHome'].setEnabled(1)
        else:
            self.gui.actions['goHome'].setEnabled(0)


    def updateForward(self, available) :
        """Enables/disables the Go --> Forward menu item."""
        self.gui.actions['goForward'].setEnabled(available)


    def updateBackward(self, available) :
        """Enables/disables the Go --> Backward menu item."""
        self.gui.actions['goBackward'].setEnabled(available)

    #########################################################
    #
    # 					Bookmarks menu related slots
    #
    #########################################################

    def addBookmark(self) :
        """
        Add the current page to the bookmarks menu.

        Bookmarks --> Add bookmark
        """

        src = self.gui.text_browser.source().toString()
        src = QtCore.QDir().fromNativeSeparators(src)
        src = unicode(src).replace('///', '/')
        if self.bookmarks.count(src) :
            # if the page is already bookmarked we do nothing
            pass
        else :
            # The page is not bookmarked so we append it to the bookmarks list.
            self.bookmarks.append(src)


    def editBookmarks(self) :
        """
        Edit bookmarks.

        Bookmarks --> Edit bookmarks
        """

        # update bookmarks list
        edit_dlg = bookmarksDlg.BookmarksDlg(self.bookmarks, self.gui)
        edit_dlg.exec_()


    def clearBookmarks(self) :
        """Clear all bookmarks."""
        self.bookmarks.clear()

    #########################################################
    #
    # 					History related slots
    #
    #########################################################

    def clearHistory(self) :
        """
        Clear the history of visited documents.

        Toolbar --> Clear History
        """

        self.history.clear()
        self.gui.combo_history.clear()
        self.updateHome()


    def updateHistory(self, src) :
        """
        Updates the contents of the combo selector.

        Combo selector has to be updated when:

        - a new file is opened
        - a link is clicked in the current document
        - a bookmark is opened

        The history combobox is a visual representation of the history
        list, so entries will occupy the same position in both, the
        list and the combo.

        :Parameter src: the path being added to the combo
        """

        url = src.toString()
        url = QtCore.QDir().fromNativeSeparators(url)
        url = unicode(url).replace('///', '/')
        if not self.history.count(url):
            self.history.append(url)
            self.gui.combo_history.addItem(url)

        self.gui.combo_history.setCurrentIndex(self.history.indexOf(url))
        self.updateHome()

    #########################################################
    #
    # 					Help menu related slots
    #
    #########################################################

    def aboutBrowser(self) :
        """
        Shows a message box with the application ``About`` info.

        Help --> About HelpBrowser
        """

        QtGui.QMessageBox.information(self.gui, \
            trs('About HelpBrowser', 'A dialog caption'), 
            trs("""<html><h3>HelpBrowser</h3>
                HelpBrowser is a very simple tool for displaying the HTML
                version of the ViTables' Guide without using external programs.
                <p>Best of all... it is written using PyQt, the Python
                bindings for the Qt GUI toolkit.</html>""",
                'About Help browser text')
            )


    def aboutQt(self) :
        """
        Shows a message box with the ``Qt About`` info.

        Help --> About Qt
        """

        caption = trs('About Qt', 'A dialog caption')
        QtGui.QMessageBox.aboutQt(self.gui, caption)
