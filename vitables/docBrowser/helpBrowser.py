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
Here is defined the HelpBrowser class.

Classes:

* HelpBrowser(QObject) 

Methods:

* __init__(self, vtapp) 
* __tr(self, source, comment=None)
* connectSignals(self)
* slotDisplaySrc(self, src=None)
* slotNewBrowser(self)
* slotOpenFile(self, filepath=None)
* slotCloseWindow(self)
* slotExitBrowser(self)
* slotZoomIn(self) 
* slotZoomOut(self) 
* updateHome(self) 
* slotUpdateForward(self, available)
* slotUpdateBackward(self, available)
* slotRecentSubmenuAboutToShow(self)
* slotOpenBookmark(self, bmark_id)
* slotAddBookmark(self)
* slotEditBookmarks(self)
* slotClearBookmarks(self)
* slotClearHistory(self)
* updateHistory(self, src) 
* slotAboutHelpBrowser(self)
* slotAboutQt(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'HelpBrowser'

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils
from vitables.vtSite import *
from vitables.docBrowser import bookmarksDlg
from vitables.docBrowser import browserGUI

class HelpBrowser(QObject) :
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

    def __init__(self, vtapp) :
        """
        Initializes the browser.

        Restore history and bookmarks from disk and makes the browser window.

        :Parameter vtapp: an instance of `VTApp`
        """

        QObject.__init__(self)

        self.vtapp = vtapp

        # Get the bookmarks and the navigation history
        self.bookmarks = vtapp.hb_bookmarks
        self.history = vtapp.hb_history

        # create the GUI
        self.gui = browserGUI.HelpBrowserGUI(self)

        # The working directory used in QFileDialog calls
        self.working_dir = vitables.utils.getHomeDir()

        # Connect signals to slots
        self.connectSignals()

        # The GUI setup is slow so it is not shown until the setup is
        # done (it avoids displaying an ugly empty widget)
        self.slotDisplaySrc('index.html')
        self.gui.show()


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def connectSignals(self):
        """
        Connect signals to slots.

        Signals coming from the menubar and toolbars are connected to
        slots of the documentation browser controller (`HelpBrowser`).
        """

        self.connect(self.gui.combo_history, 
            SIGNAL('activated(QString)'), self.slotDisplaySrc)

        # This is the most subtle connection. It encompasses source
        # changes coming from anywhere, including slots (home, backward
        # and forward), menus (Go and Bookmarks), clicked links and
        # programatic changes (setSource calls).
        self.connect(self.gui.text_browser, 
            SIGNAL('sourceChanged(QUrl)'), 
            self.updateHistory)

        self.connect(self.gui.text_browser, 
            SIGNAL('backwardAvailable(bool)'), 
            self.slotUpdateBackward)

        self.connect(self.gui.text_browser, 
            SIGNAL('forwardAvailable(bool)'), 
            self.slotUpdateForward)

        self.connect(self.gui.bookmarks_menu, 
            SIGNAL('aboutToShow()'), 
            self.slotRecentSubmenuAboutToShow)


    def slotDisplaySrc(self, src=None):
        """
        Displays a document in the `HelpBrowser` window.

        :Parameter src: the path of the file being displayed
        """

        # If a bookmark or an item from the combo history is being loaded
        if src is None:
            action = self.gui.sender()
            action_text = action.text()
            if action_text.count(QRegExp("^\d")):
                src = action_text.remove(QRegExp("^\d+\.\s+"))

        src = QDir().fromNativeSeparators(src) # src can be a QString
        basename = os.path.basename(unicode(src))
        url = QUrl(os.path.join(DOCDIR, basename))
        self.gui.text_browser.setSource(url)

    #########################################################
    #
    # 					File menu related slots
    #
    #########################################################

    def slotNewBrowser(self) :
        """
        Opens a new help browser window.

        File --> New Window

        Creates a new `HelpBrowser` instance and shows it. The new instance is
        appended to the list of opened browsers. This way we can keep track of
        the opened windows, what is needed when we quit the browser.
        """

        browser = HelpBrowser(self.vtapp)
        self.vtapp.doc_browsers.append(browser)


    def slotOpenFile(self, filepath=None) :
        """
        Shows a file in the help browser window.

        File --> Open File

        :Parameter filepath: the path of the file being open
        """

        file_dlg = QFileDialog(self.gui)
        file_dlg.setFilters(QStringList(self.__tr(
            """HTML files (*.html *.htm);;"""
            """Any file (*.*)""", 'File filter for the Open File dialog')))
        file_dlg.setWindowTitle(self.__tr('Select a file for opening', 
            'A dialog caption'))
        file_dlg.setDirectory(self.working_dir)
        try:

            # OK clicked. Working directory is updated
            if file_dlg.exec_():
                # The absolut path of the selected file
                filepath = file_dlg.selectedFiles()[0]
                # Update the working directory
                self.working_dir = \
                    unicode(file_dlg.directory().canonicalPath())
                # Displays the document (history is automatically updated)
                self.slotDisplaySrc(filepath)
            # Cancel clicked. Working directory doesn't change
            else:
                pass
        finally:
            del file_dlg


    def slotCloseWindow(self) :
        """
        Close the active window.

        File --> Close Window

        The generated close event is processed by the reimplemented handler
        """

        self.vtapp.hb_history = self.history
        self.vtapp.hb_bookmarks = self.bookmarks
        self.gui.close()


    def slotExitBrowser(self) :
        """
        Quit the HelpBrowser.

        File --> Exit

        Before to quit, session and bookmarks must be saved. Then all browser
        windows are closed.
        We save the state of the window on which exit is invoqued.
        """

        # Close all browsers
        for browser in self.vtapp.doc_browsers[:] :
            browser.slotCloseWindow()

    #########################################################
    #
    # 					View menu related slots
    #
    #########################################################

    def slotZoomIn(self) :
        """Increases the font size of the displayed source."""
        self.gui.text_browser.zoomIn(2)


    def slotZoomOut(self) :
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


    def slotUpdateForward(self, available) :
        """Enables/disables the Go --> Forward menu item."""
        self.gui.actions['goForward'].setEnabled(available)


    def slotUpdateBackward(self, available) :
        """Enables/disables the Go --> Backward menu item."""
        self.gui.actions['goBackward'].setEnabled(available)

    #########################################################
    #
    # 					Bookmarks menu related slots
    #
    #########################################################

    def slotRecentSubmenuAboutToShow(self):
        """Update the content of the Bookmarks menu."""

        # Clear the last bookmarks menu...
        menu_actions = self.gui.bookmarks_menu.actions()
        for action in menu_actions:
            if action.text().count(QRegExp("^\d")):
                self.gui.bookmarks_menu.removeAction(action)
        # and refresh it
        index = 0
        for item in self.bookmarks:
            index += 1
            filepath = unicode(item)
            action = QAction('%s. %s' % (index, filepath), 
                                               self.gui.bookmarks_menu)
            action.setData(QVariant(item))
            self.gui.connect(action, SIGNAL("triggered()"), 
                self.slotDisplaySrc)
            self.gui.bookmarks_menu.addAction(action)


    def slotOpenBookmark(self, bmark_id) :
        """
        Displays a bookmark in the `HelpBrowser` window.

        Bookmarks --> menu item selected

        A Bookmarks menu item has the format ``<position shortName>``.
        Selecting an item from the bookmarks list based on the shortname
        is not reliable because more than one item can have the same
        shortname, instead we will take advantage from the fact that
        item list position equals to item menu identifier minus 1.

        :Parameter bmark_id: the bookmark identifier
        """

        bmark = self.bookmarks[bmark_id - 1]
        self.slotDisplaySrc(bmark) # SIGNAL sourceChanged() emited


    def slotAddBookmark(self) :
        """
        Add the current page to the bookmarks menu.

        Bookmarks --> Add bookmark
        """

        src = self.gui.text_browser.source().toString(QUrl.RemoveScheme)
        src = vitables.utils.forwardPath(unicode(src))
        src = src.replace('///', '/')
        if self.bookmarks.count(src) :
            # if the page is already bookmarked we do nothing
            pass
        else :
            # The page is not bookmarked so we append it to the bookmarks list.
            self.bookmarks.append(src)


    def slotEditBookmarks(self) :
        """
        Edit bookmarks.

        Bookmarks --> Edit bookmarks
        """

        # update bookmarks list
        edit_dlg = bookmarksDlg.BookmarksDlg(self.bookmarks, self.gui)
        edit_dlg.exec_()


    def slotClearBookmarks(self) :
        """Clear all bookmarks."""
        self.bookmarks.clear()

    #########################################################
    #
    # 					History related slots
    #
    #########################################################

    def slotClearHistory(self) :
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

        url = QUrl(src).toString(QUrl.RemoveScheme)
        url = QDir().fromNativeSeparators(url)
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

    def slotAboutHelpBrowser(self) :
        """
        Shows a message box with the application ``About`` info.

        Help --> About HelpBrowser
        """

        caption = self.__tr('About HelpBrowser', 'A dialog caption')
        text = self.__tr(
            """<qt>
            <h3>HelpBrowser</h3>
            HelpBrowser is a very simple tool for displaying local Qt
            rich text files. It is also reasonably capable for browsing
            HTML files.
            <p>Best of all... It is written using PyQt, the Python
            bindings for the Qt GUI toolkit. :-)
            </qt>""",
            'About Help browser text')

        # Display a customized About dialog
        about = QMessageBox(caption, text, 
            QMessageBox.Information, 
            QMessageBox.NoButton, QMessageBox.NoButton, 
            QMessageBox.NoButton, self.gui)
        # Show the message
        about.show()

    def slotAboutQt(self) :
        """
        Shows a message box with the ``Qt About`` info.

        Help --> About Qt
        """

        caption = self.__tr('About Qt', 'A dialog caption')
        QMessageBox.aboutQt(self.gui, caption)
