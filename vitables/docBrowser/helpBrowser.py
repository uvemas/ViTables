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
#       $Id: helpBrowser.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the HelpBrowser class.

Classes:

* HelpBrowser(qt.QObject) 

Methods:

* __init__(self, parent) 
* __tr(self, source, comment=None)
* connectSignals(self)
* slotNewBrowser(self) 
* slotOpenFile(self, filepath=None) 
* slotCloseWindow(self) 
* slotExitBrowser(self) 
* slotZoomIn(self) 
* slotZoomOut(self) 
* updateHome(self) 
* slotUpdateForward(self, available) 
* slotUpdateBackward(self, available) 
* slotUpdateBookmarksMenu(self) 
* slotOpenBookmark(self, bmark_id) 
* slotAddBookmark(self) 
* slotEditBookmarks(self) 
* slotClearBookmarks(self) 
* slotDisplaySrc(self, src) 
* slotClearHistory(self) 
* updateHistory(self, src) 
* slotAboutHelpBrowser(self) 
* slotAboutQt(self) 

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os

import qt

import vitables.utils
from vitables.docBrowser import bookmarksDlg
from vitables.docBrowser import browserGUI

class HelpBrowser(qt.QObject) :
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


    def __init__(self, parent) :
        """
        Initializes the browser.

        Restore history and bookmarks from disk and makes the browser window.
        
        :Parameter parent: is an instance of `VTApp`
        """

        qt.QObject.__init__(self)

        self.vtapp = parent

        # Get the bookmarks and the navigation history
        self.bookmarks = parent.hbBookmarks
        self.history = parent.hbHistory

        # The User's Guide file
        self.users_guide = vitables.utils.forwardPath(
            os.path.join(self.vtapp.config.doc_dir, 'html', 'index.html'))
        self.not_found_doc = vitables.utils.forwardPath(os.path.abspath(
            os.path.join(self.vtapp.config.doc_dir, 'html', 'not_found.html')))

        # create the GUI
        self.gui = browserGUI.HelpBrowserGUI(self, 
            self.vtapp.config.doc_dir, self.vtapp.config.icons_dir)
        
        # The working directory used in QFileDialog calls
        self.lastOpenDir = vitables.utils.getHomeDir()

        # Connect signals to slots
        self.actions = self.gui.actions
        self.connectSignals()

        # The GUI setup is slow so it is not shown until the setup is
        # done (it avoids displaying an ugly empty widget)
        self.slotDisplaySrc(self.users_guide)
        self.gui.show()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('HelpBrowser', source, comment).latin1()


    def connectSignals(self):
        """
        Connect signals to slots.

        Signals coming from the menubar and toolbars are connected to
        slots of the documentation browser controller (`HelpBrowser`).
        """

        self.connect(self.gui.comboHistory, 
            qt.SIGNAL('activated(const QString &)'), self.slotDisplaySrc)

        # This is the most subtle connection. It encompasses source
        # changes  coming from anywhere, including slots (home, backward
        # and forward),  menus (Go and Bookmarks) clicked links and
        # programatic changes.
        self.connect(self.gui.text_browser, qt.SIGNAL('sourceChanged(const QString &)'), 
            self.updateHistory)

        self.connect(self.gui.text_browser, qt.SIGNAL('backwardAvailable(bool)'), 
            self.slotUpdateBackward)

        self.connect(self.gui.text_browser, qt.SIGNAL('forwardAvailable(bool)'), 
            self.slotUpdateForward)

        self.connect(self.gui.bookmarks_menu, qt.SIGNAL('aboutToShow()'), 
            self.slotUpdateBookmarksMenu)

        # Connect actions to slots
        # The actions are defined in the browserGUI module
        action_signal_slot = {
            #
            # File menu
            #
            'newBrowser':
            (self.actions['newBrowser'], qt.SIGNAL('activated()'),
                self.slotNewBrowser),
            'openFile':
            (self.actions['openFile'], qt.SIGNAL('activated()'),
                self.slotOpenFile),
            'closeWindow':
            (self.actions['closeWindow'], qt.SIGNAL('activated()'),
                self.slotCloseWindow),
            'exitBrowser':
            (self.actions['exitBrowser'], qt.SIGNAL('activated()'),
                self.slotExitBrowser),
            #
            # View menu
            #
            'zoomIn':
            (self.actions['zoomIn'], qt.SIGNAL('activated()'), 
                self.slotZoomIn),
            'zoomOut':
            (self.actions['zoomOut'], qt.SIGNAL('activated()'), 
                self.slotZoomOut),
            #
            # Go menu
            #
            'goHome':
            (self.actions['goHome'], qt.SIGNAL('activated()'), self.gui.text_browser,
                qt.SLOT('home()')),
            'goBackward':
            (self.actions['goBackward'], qt.SIGNAL('activated()'), self.gui.text_browser,
                qt.SLOT('backward()')),
            'goForward':
            (self.actions['goForward'], qt.SIGNAL('activated()'), self.gui.text_browser,
                qt.SLOT('forward()')),
            'goReload':
            (self.actions['goReload'], qt.SIGNAL('activated()'), self.gui.text_browser,
                qt.SLOT('reload()')),
            #
            # Bookmarks menu
            #
            'bookmarksAdd': 
            (self.actions['bookmarksAdd'], qt.SIGNAL('activated()'),
                self.slotAddBookmark),
            'bookmarksEdit': 
            (self.actions['bookmarksEdit'], qt.SIGNAL('activated()'),
                self.slotEditBookmarks),
            'bookmarksClear': 
            (self.actions['bookmarksClear'], qt.SIGNAL('activated()'),
                self.slotClearBookmarks),
            #
            # Help menu
            #
            'about': 
            (self.actions['about'], qt.SIGNAL('activated()'),
                self.slotAboutHelpBrowser),
            'aboutQt': 
            (self.actions['aboutQt'], qt.SIGNAL('activated()'),
                self.slotAboutQt),
            #
            # Navigation toolbar
            #
            'clearSession': 
            (self.actions['clearSession'], qt.SIGNAL('activated()'),
                self.slotClearHistory)
            }

        for args in action_signal_slot.values() :
            apply(self.connect, args)


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
        self.vtapp.docBrowsers.append(browser)


    def slotOpenFile(self, filepath=None) :
        """
        Shows a file in the help browser window.

        File --> Open File

        :Parameter filepath: the path of the file being open
        """

        fileDlg = qt.QFileDialog(self.gui, None, 1)
        fileDlg.setFilters(self.__tr("""HTML files (*.html *.htm);;"""
            """Any file (*.*)""", 'File filter for the Open File dialog'))
        fileDlg.setCaption(self.__tr('Select a file for opening', 
            'A dialog caption'))
        fileDlg.setDir(self.lastOpenDir)
        try:
            fileDlg.exec_loop()
            # OK clicked. Working directory is updated
            if fileDlg.result() == qt.QDialog.Accepted:
                # The absolut path of the selected file
                filepath = fileDlg.selectedFile()
                # Update the working directory
                self.lastOpenDir = fileDlg.dir().canonicalPath().latin1()
                # Displays the document (it will automatically update the history)
                self.slotDisplaySrc(filepath)
            # Cancel clicked. Working directory doesn't change
            else:
                pass
        finally:
            del fileDlg

    
    def slotCloseWindow(self) :
        """
        Close the active window.

        File --> Close Window

        The generated close event is processed by the reimplemented handler
        """

        self.vtapp.hbHistory = self.history
        self.vtapp.hbBookmarks = self.bookmarks
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
        for browser in self.vtapp.docBrowsers[:] :
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
    
    def slotUpdateBookmarksMenu(self) :
        """
        Updates the content of the Bookmarks menu.

        Every time the menu is poped its content is synchronized with the
        content of the bookmarks file. This ensures that all opened help
        browser windows will have the same bookmarks menu. The bookmarks
        menu is a visual representation of the bookmarks file, so
        bookmarks will occupy the same position in both, the file and the menu
        (well, with a shifting of 3 positions due to the fixed items of the
        bookmarks menu).
        """

        self.gui.bookmarks_menu.clear()
        # Adds items to menu
        for action_def in self.gui.bookmarks_menu_actions :
            action_id = action_def[0]
            self.gui.actions[action_id].addTo(self.gui.bookmarks_menu)

        self.gui.bookmarks_menu.setId(0, 1000)
        self.gui.bookmarks_menu.setId(1, 2000)
        self.gui.bookmarks_menu.setId(1, 3000)
        self.gui.bookmarks_menu.insertSeparator()

        # The jth bookmarks list item will have an identifier item_id=j + 1
        item_id = 1
        for filepath in self.bookmarks :
            shortname = os.path.basename(filepath)
            self.gui.bookmarks_menu.insertItem('%d %s' % (item_id, shortname), 
                item_id)
            self.gui.bookmarks_menu.connectItem(item_id, self.slotOpenBookmark)
            item_id = item_id + 1


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

        src_path = self.bookmarks[bmark_id - 1]
        self.slotDisplaySrc(src_path) # qt.SIGNAL sourceChanged() emited


    def slotAddBookmark(self) :
        """
        Add the current page to the bookmarks menu.

        Bookmarks --> Add bookmark
        """

        src = self.gui.text_browser.source().latin1()
        src = vitables.utils.forwardPath(os.path.abspath(src))
        if src in self.bookmarks :
            # if the page is already bookmarked we do nothing
            pass
        else :
            # The page is not bookmarked so we append it to the bookmarks list.
            # We dont need to add it to the Bookmarks menu, it will be done via 
            # slotUpdateBookmarksMenu
            self.bookmarks.append(src)


    def slotEditBookmarks(self) :
        """
        Edit bookmarks.

        Bookmarks --> Edit bookmarks
        """

        # update bookmarks list
        edit_dlg = bookmarksDlg.BookmarksDlg(self.bookmarks, self.gui)
        edit_dlg.exec_loop()


    def slotClearBookmarks(self) :
        """Clear all bookmarks."""
        self.bookmarks = []


    #########################################################
    #
    # 					History related slots
    #
    #########################################################
    
    def slotDisplaySrc(self, src) :
        """
        Displays a document in the `HelpBrowser` window.

        :Parameter src: the combo item text
        """

        if isinstance(src, qt.QString):
            src = src.latin1()

        # The source can be a bookmarked page so we have to extract
        # the filepath
        filepath = src.split('#')[0]
        if os.path.isfile(filepath):
            self.gui.text_browser.setSource(src)
            self.gui.text_browser.update()
        else:
            self.gui.text_browser.setSource(self.not_found_doc)


    def slotClearHistory(self) :
        """
        Clear the history of visited documents.

        Toolbar --> Clear History
        """

        self.history = []
        self.gui.comboHistory.clear()
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

        src = vitables.utils.forwardPath(os.path.abspath(src.latin1()))
        if src == self.not_found_doc:
            return
        if not src in self.history:
            self.history.append(src)
            self.gui.comboHistory.insertItem(src)

        self.gui.comboHistory.setCurrentItem(self.history.index(src))
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
        about = qt.QMessageBox(caption, text, qt.QMessageBox.Information, 
            qt.QMessageBox.NoButton, qt.QMessageBox.NoButton, 
            qt.QMessageBox.NoButton, self.gui)
        # Show the message
        about.show()


    def slotAboutQt(self) :
        """
        Shows a message box with the ``Qt About`` info.

        Help --> About Qt
        """

        caption = self.__tr('About Qt', 'A dialog caption')
        qt.QMessageBox.aboutQt(self.gui, caption)
