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
Here is defined the BookmarksDlg class.

This module provides a dialog for deleting bookmarks from the bookmarks list.
"""

__docformat__ = 'restructuredtext'

import sys
import os.path

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

translate = QtWidgets.QApplication.translate


class BookmarksDlg(QtWidgets.QDialog):
    """
    The dialog for deleting bookmarks.

    The class defines a modal dialog used to delete entries from the
    bookmarks list. Bookmarks are displayed in a tree view. As a bonus, they
    can be visited directly from this dialog by double clicking them in the
    tree. At the bottom there is a group of buttons made of the ``Delete``,
    ``OK`` and ``Cancel`` buttons.
    ``Delete`` removes checked items from the bookmarks list.

    :Parameters:

    - `blist`: the bookmarks list
    - `hbgui`: an instance of
      :meth:`vitables.docbrowser.browsergui.HelpBrowserGUI` (the parent widget)
    """

    def __init__(self, blist, hbgui):
        """
        Dialog constructor.
        """

        # The HelpBrowser GUI instance from which this dialog has been opened
        super(BookmarksDlg, self).__init__(hbgui)

        self.setWindowTitle(
            translate('BookmarksDlg', 'Bookmarks editor', 'Dialog caption'))
        dlg_layout = QtWidgets.QVBoxLayout(self)

        # Add a tree view
        self.tree = QtWidgets.QTreeView(self)
        self.tree.setItemsExpandable(False)
        self.tmodel = QtGui.QStandardItemModel()
        self.tree.setModel(self.tmodel)
        self.tmodel.setHorizontalHeaderLabels([
            translate('BookmarksDlg', 'Bookmark',
            'First column header of the bookmarks table'),
            translate('BookmarksDlg', 'URL',
            'Second column header of the bookmarks table')])
        dlg_layout.addWidget(self.tree)

        # Add a group of buttons
        self.button_group = QtWidgets.QDialogButtonBox(self)
        self.ok_button = self.button_group.addButton(
            translate('BookmarksDlg', '&OK', 'Button label'),
            QtWidgets.QDialogButtonBox.AcceptRole)
        self.del_button = self.button_group.addButton(
            translate('BookmarksDlg', '&Delete', 'Button label'),
            QtWidgets.QDialogButtonBox.ActionRole)
        self.cancel_button = self.button_group.addButton(
            translate('BookmarksDlg', '&Cancel', 'Button label'),
            QtWidgets.QDialogButtonBox.RejectRole)
        dlg_layout.addWidget(self.button_group)

        # We dont work directly on the HelpBrowser bookmarks list,
        # instead we make a copy. This is convenient if, after doing
        # some changes in the list, we decide to cancel the changes.
        self.blist = blist[:]
        self.fillBookmarksTable()
        self.show()

        # Finally we connect signals to slots
        self.tmodel.itemChanged.connect(self.updateDeleteButton)
        self.tree.doubleClicked.connect(self.displayBookmark)
        self.button_group.clicked.connect(self.buttonClicked)

        self.del_button.setEnabled(False)


    def fillBookmarksTable(self):
        """Add entries to the bookmarks table."""

        self.tmodel.setColumnCount(2)
        parent_item = self.tmodel.invisibleRootItem()
        # Each item of the tree (bookmark) is extracted from the bookmarks list
        for entry in self.blist :
            # extracts the short name. Examples:
            # /home/vmas/estilo.html --> estilo.html
            # /home/vmas/estilo.html#color --> estilo.html#color
            shortname = os.path.basename(entry)
            item = QtGui.QStandardItem(shortname)
            item.setCheckable(True)
            item.setEditable(False)
            item1 = QtGui.QStandardItem(entry)
            item1.setEditable(False)
            parent_item.appendRow([item, item1])
        self.tree.setExpanded(self.tmodel.indexFromItem(parent_item), True)
        self.tree.repaint()
        self.repaint()


    def displayBookmark(self, index):
        """
        Display a given bookmark in the help browser.

        When a bookmark is double clicked the `HelpBrowser` window is
        updated and displays that bookmark.

        :Parameter index: the index in the bookmarks tree view of the selected
          bookmark
        """

        # Get the bookmark UID
        row = self.tmodel.itemFromIndex(index).row()
        src = self.blist[row]
        self.parent().browser.displaySrc(src)


    def updateDeleteButton(self, item):
        """
        Enable/disable the ``Delete`` button.

        The state of the ``Delete`` button depends on the presence/abscence
        of checked items in the bookmarks list. Every time an item is
        clicked the whole bookmarks tree is traversed looking for checked
        items. The``Delete`` button state is updated accordingly.

        :Parameter item: the bookmarks tree item checked/unchecked
        """

        parent_item = self.tmodel.invisibleRootItem()
        # Iterate over the QTreeWidget looking for checked items
        enabled = 0
        row = 0
        item = parent_item.child(row)
        while item != None:
            if item.checkState() == QtCore.Qt.Checked:
                enabled = 1
                break
            row = row + 1
            item = parent_item.child(row)

        self.del_button.setEnabled(enabled)


    def buttonClicked(self, button):
        """
        Action selector method.

        Depending on the button clicked in the button group the
        appropriate method is called.

        :Parameter button: the clicked button
        """

        role = self.button_group.buttonRole(button)
        # OK button clicked
        if role == QtWidgets.QDialogButtonBox.AcceptRole:
            gui = self.parent()
            gui.browser.bookmarks = self.blist
            self.accept()
        # Delete button clicked
        elif role == QtWidgets.QDialogButtonBox.ActionRole:
            self.deleteBookmarks()
        # Cancel button clicked
        elif role == QtWidgets.QDialogButtonBox.RejectRole:
            self.reject()


    def deleteBookmarks(self) :
        """Delete all selected bookmarks."""

        parent_item = self.tmodel.invisibleRootItem()
        # Iterate over the QTreeView looking for checked items
        deleted_rows = []
        row = 0
        item = parent_item.child(row)
        while item != None:
            if item.checkState() == QtCore.Qt.Checked:
                deleted_rows.append(row)
            row = row + 1
            item = parent_item.child(row)
        # Items with highest model indexes are removed first from the model
        # This way deleting an item does not modify the model index of the
        # remaining items
        deleted_rows.reverse()
        for row in deleted_rows:
            self.tmodel.takeRow(row)
            del self.blist[row]

        # After deletion we udpate the dialog
        self.del_button.setEnabled(0)

if __name__ == '__main__':
    APP = QtWidgets.QApplication(sys.argv)
    DLG = BookmarksDlg(['uno', 'dos'], None)
    APP.exec_()
