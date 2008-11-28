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
#       $Id: bookmarksDlg.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the BookmarksDlg class.

Classes:

* BookmarksDlg(qt.QDialog)

Methods:

* __init__(self, blist, hbgui)
* __tr(self, source, comment=None)
* makePage(self)
* fillBookmarksTable(self)
* slotDisplayBookmark(self, lvi)
* slotCheckDeleteButton(self, lvi)
* slotButtonClicked(self, button)
* slotDeleteBookmarks(self) 

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys
import os.path

import qt

class BookmarksDlg(qt.QDialog):
    """
    The dialog for editing bookmarks.

    The class defines a modal dialog used to delete entries from the
    bookmarks list.
    Bookmarks are displayed in a tree view with `QListView`. Each
    bookmark is a `QCheckListItem`. At the bottom there is a group of
    buttons with ``Delete``, ``OK`` and ``Cancel`` buttons. ``Delete``
    removes checked items from the bookmarks list. 
    """


    def __init__(self, blist, hbgui):
        """
        Dialog constructor.
        
        :Parameters:

        `blist`: the bookmarks list
        `hbgui`: an instance of HelpBrowserGUI (the parent widget)
        """

        # The HelpBrowser GUI instance from which this dialog has been opened
        
        qt.QDialog.__init__(self, hbgui)

        self.setCaption(self.__tr('Bookmarks editor', 'Dialog caption'))
        self.setWFlags(qt.Qt.WDestructiveClose)

        # Give a layout to the dialog
        self.dlg_layout = qt.QVBoxLayout(self, 10, 6)

        # Arrange the dialog components
        self.blv = qt.QListView(self)
        self.button_group = qt.QButtonGroup(3, qt.Qt.Horizontal, self)
        self.ok_button = qt.QPushButton(self.__tr('&OK', 'Button label'), \
            self.button_group)  # ID=0
        self.del_button = qt.QPushButton(self.__tr('&Delete', 'Button label'), \
            self.button_group)  # ID=1
        self.cancel_button = \
            qt.QPushButton(self.__tr('&Cancel', 'Button label'), \
            self.button_group)  # ID=2
        self.makePage()

        # We dont work directly on the HelpBrowser bookmarks list,
        # instead we make a copy. This is convenient if, after doing
        # some changes in the list, we  decide to cancel the changes.
        self.blist = blist[:]
        self.fillBookmarksTable()

        # Finally we connect signals to slots
        self.connect(self.blv, qt.SIGNAL('clicked(QListViewItem *)'),
            self.slotCheckDeleteButton)
        self.connect(self.blv, qt.SIGNAL('doubleClicked(QListViewItem *)'),
            self.slotDisplayBookmark)
        self.connect(self.button_group, qt.SIGNAL('clicked(int)'),
            self.slotButtonClicked)

        self.blv.emit(qt.SIGNAL('clicked(QListViewItem *)'), (None,))


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('BookmarksDlg', source, comment).latin1()


    def makePage(self):
        """
        Add components to the bookmarks dialog.

        The dialog is made of a `QListView`, that displays the list
        of bookmarks in a tabular way, and several buttons.
        The bookmarks table has two columns, ``Name`` and ``URL``, that
        show the short name and the full path of a document section.
        For instance the section ``/usr/share/data/style.html#colors``
        has ``URL`` ``/usr/share/data/style.html#colors`` and ``Name``
        ``style.html#colors``
        """

        #
        #				QListView
        #

        self.dlg_layout.addWidget(self.blv)
        self.blv.addColumn(self.__tr('Bookmark', 
            'First column header of the bookmarks table'))
        self.blv.addColumn(self.__tr('URL', 
            'Second column header of the bookmarks table'))
    
        #
        #				QButtonGroup
        #

        self.button_group.setFrameStyle(qt.QFrame.NoFrame)
        self.ok_button.setDefault(1)

        # Layout the buttons in such a way that they dont become wider
        # when the dialog is horizontally expanded
        buttons_layout = qt.QHBoxLayout(self.dlg_layout)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.button_group)
        buttons_layout.addStretch(1)


    def fillBookmarksTable(self):
        """Add entries to the bookmarks table."""

        # Each item of the tree (bookmark) is extracted from the bookmarks list
        for item in self.blist :
            # extracts the short name. Examples:
            # /home/vmas/estilo.html --> estilo.html
            # /home/vmas/estilo.html#color --> estilo.html#color
            shortname = os.path.basename(item)

            # construct a checkable list view item
            lvi = qt.QCheckListItem(self.blv, shortname, \
                qt.QCheckListItem.CheckBox)
            lvi.setText(1, item)
            self.blv.insertItem(lvi)


    def slotDisplayBookmark(self, lvi):
        """
        Display a given bookmark in the help browser.
        
        When a bookmark is double clicked the `HelpBrowser` window is
        updated and displays that bookmark.
        """

        # The HelpBrowser instance tied to this dialog
        help_browser = self.parent().helpBrowser
        # Get the bookmark ID
        src = lvi.text(1).latin1()
        bookmark_id = help_browser.bookmarks.index(src)
        # Open the bookmark
        help_browser.slotOpenBookmark(bookmark_id + 1)


    def slotCheckDeleteButton(self, lvi):
        """
        Enable/disable the ``Delete`` button.
        
        The state of the ``Delete`` button depends on the presence/abscence
        of checked items in the bookmarks list. Every time an item is
        clicked the ``Delete`` button state is updated.
        """

        # Iterate over the QListView looking for checked items
        enabled = 0
        current = self.blv.firstChild()
        while current :
            if current.isOn() :
                enabled = 1
                break
            else :
                current = current.nextSibling()

        self.del_button.setEnabled(enabled)


    def slotButtonClicked(self, button):
        """
        Action selector method.

        Depending on the button clicked in the button group the
        appropriate method is called.
        """

        # OK button clicked
        if button == 0:
            gui = self.parent()
            gui.helpBrowser.bookmarks = self.blist
            self.accept()
        # Delete button clicked
        elif button == 1:
            self.slotDeleteBookmarks()
        # Cancel button clicked
        elif button == 2:
            self.reject()


    def slotDeleteBookmarks(self) :
        """Delete all selected bookmarks."""

        # Return if the bookmarks list is empty
        if not self.blv.childCount() :
            return

        # Iterate over the QListView and delete the checked items
        current = self.blv.firstChild()
        while current :
            if current.isOn() :
                next_current = current.nextSibling()
                # from the QListViewItem gets the full name of the bookmark
                full_name = current.text(1)
                # and remove it from the bookmarks list
                self.blist.remove(full_name)
                # finally remove the item from the QListView
                self.blv.takeItem(current)
                del current
                current = next_current
            else :
                current = current.nextSibling()

        # After deletion we udpate the dialog
        self.blv.repaintContents()
        self.del_button.setEnabled(0)


if __name__ == '__main__' :
    APP = qt.QApplication(sys.argv)
    APP.connect(APP, qt.SIGNAL('lastWindowClosed()'), APP, qt.SLOT('quit()'))
    BDLG = BookmarksDlg([])
    BDLG.exec_loop()
    APP.exec_loop()
