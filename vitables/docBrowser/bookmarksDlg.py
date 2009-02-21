#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
Here is defined the BookmarksDlg class.

Classes:

* BookmarksDlg(QDialog)

Methods:

* __init__(self, blist, hbgui)
* __tr(self, source, comment=None)
* fillBookmarksTable(self)
* slotDisplayBookmark(self, index)
* slotCheckDeleteButton(self, item)
* slotButtonClicked(self, button)
* deleteBookmarks(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import sys
import os.path

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class BookmarksDlg(QDialog):
    """
    The dialog for editing bookmarks.

    The class defines a modal dialog used to delete entries from the
    bookmarks list.
    Bookmarks are displayed in a tree view with `QTreeView`. Bookmarks
    can be visited by double clicking them. At the bottom there is a group of
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
        QDialog.__init__(self, hbgui)

        self.setWindowTitle(self.__tr('Bookmarks editor', 'Dialog caption'))
        dlg_layout = QVBoxLayout(self)

        # Add a tree view
        self.tree = QTreeView(self)
        self.tree.setItemsExpandable(False)
        self.model = QStandardItemModel()
        self.tree.setModel(self.model)
        self.model.setHorizontalHeaderLabels([
            self.__tr('Bookmark', 
            'First column header of the bookmarks table'), 
            self.__tr('URL', 
            'Second column header of the bookmarks table')])
        dlg_layout.addWidget(self.tree)

        # Add a group of buttons
        self.button_group = QDialogButtonBox(self)
        self.ok_button = self.button_group.addButton(self.__tr('&OK', 
            'Button label'), QDialogButtonBox.AcceptRole)
        self.del_button = self.button_group.addButton(self.__tr('&Delete', 
            'Button label'), QDialogButtonBox.ActionRole)
        self.cancel_button = self.button_group.addButton(self.__tr('&Cancel', 
            'Button label'), QDialogButtonBox.RejectRole)
        dlg_layout.addWidget(self.button_group)

        # We dont work directly on the HelpBrowser bookmarks list,
        # instead we make a copy. This is convenient if, after doing
        # some changes in the list, we decide to cancel the changes.
        self.blist = QStringList(blist)
        self.fillBookmarksTable()
        self.show()

        # Finally we connect signals to slots
        self.connect(self.model, 
            SIGNAL('itemChanged(QStandardItem *)'), 
            self.slotCheckDeleteButton)
        self.connect(self.tree, 
            SIGNAL('doubleClicked(QModelIndex)'), 
            self.slotDisplayBookmark)
        self.connect(self.button_group, 
            SIGNAL('clicked(QAbstractButton *)'), 
            self.slotButtonClicked)

        self.del_button.setEnabled(False)


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate('BookmarksDlg', source, comment))


    def fillBookmarksTable(self):
        """Add entries to the bookmarks table."""

        self.model.setColumnCount(2)
        parent_item = self.model.invisibleRootItem()
        # Each item of the tree (bookmark) is extracted from the bookmarks list
        for entry in self.blist :
            # extracts the short name. Examples:
            # /home/vmas/estilo.html --> estilo.html
            # /home/vmas/estilo.html#color --> estilo.html#color
            shortname = os.path.basename(unicode(entry))
            item = QStandardItem(shortname)
            item.setCheckable(True)
            item.setEditable(False)
            item1 = QStandardItem(entry)
            item1.setEditable(False)
            parent_item.appendRow([item, item1])
        self.tree.setExpanded(self.model.indexFromItem(parent_item), True)
        self.tree.repaint()
        self.repaint()


    def slotDisplayBookmark(self, index):
        """
        Display a given bookmark in the help browser.

        When a bookmark is double clicked the `HelpBrowser` window is
        updated and displays that bookmark.
        """

        # The HelpBrowser instance tied to this dialog
        help_browser = self.parent().browser
        # Get the bookmark UID
        row = self.model.itemFromIndex(index).row()
        src = help_browser.bookmarks[row]
        help_browser.slotDisplaySrc(src)


    def slotCheckDeleteButton(self, item):
        """
        Enable/disable the ``Delete`` button.

        The state of the ``Delete`` button depends on the presence/abscence
        of checked items in the bookmarks list. Every time an item is
        clicked the ``Delete`` button state is updated.
        """

        parent_item = self.model.invisibleRootItem()
        # Iterate over the QTreeWidget looking for checked items
        enabled = 0
        row = 0
        item = parent_item.child(row)
        while item != None:
            if item.checkState() == Qt.Checked:
                enabled = 1
                break
            row = row + 1
            item = parent_item.child(row)

        self.del_button.setEnabled(enabled)


    def slotButtonClicked(self, button):
        """
        Action selector method.

        Depending on the button clicked in the button group the
        appropriate method is called.
        """

        role = self.button_group.buttonRole(button)
        # OK button clicked
        if role == QDialogButtonBox.AcceptRole:
            gui = self.parent()
            gui.browser.bookmarks = self.blist
            self.accept()
        # Delete button clicked
        elif role == QDialogButtonBox.ActionRole:
            self.deleteBookmarks()
        # Cancel button clicked
        elif role == QDialogButtonBox.RejectRole:
            self.reject()


    def deleteBookmarks(self) :
        """Delete all selected bookmarks."""

        parent_item = self.model.invisibleRootItem()
        # Iterate over the QTreeWidget looking for checked items
        deleted_rows = []
        row = 0
        item = parent_item.child(row)
        while item != None:
            if item.checkState() == Qt.Checked:
                deleted_rows.append(row)
            row = row + 1
            item = parent_item.child(row)
        # Items with highest model indexes are removed first from the model
        # This way deleting an item does not modify the model index of the
        # remaining items
        deleted_rows.reverse()
        for row in deleted_rows:
            self.model.takeRow(row)
            del self.blist[row]

        # After deletion we udpate the dialog
        self.del_button.setEnabled(0)

if __name__ == '__main__':
    APP = QApplication(sys.argv)
    DLG = BookmarksDlg(['uno', 'dos'], None)
    APP.exec_()
