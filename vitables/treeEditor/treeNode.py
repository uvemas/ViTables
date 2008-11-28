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
#       $Id: treeNode.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the treeNode module.

Classes:

* TreeNode(qt.QListViewItem)

Methods:

* __init__(self, dbview, parent, nodename)
* getFilepath(self)
* getMode(self)
* startRename(self, column)
* okRename(self, column)
* setDnD(self, nodetype, is_root=0)
* getDnD(self)
* dragEntered(self)
* acceptDrop(self, mime_source)
* dropped(self, event)
* paintCell(self, painter, colorgr, col, width, align)

Misc variables:

* __docformat__

List view items represent nodes of the database object tree.

Drags consist in moving the source node to a new location, under the target
node, what is equivalent to move data from one location to a different one
in the database object tree. This is implemented mainly in QListView.startDrag
and QListViewItem.dropped methods, and can be achieved in several ways.

a) encoding all necessary info in startDrag method and decoding it in
dropped method.

b)encoding a source ID in the startDrag method, decoding the ID in the
dropped method and using the ID to locate the source and retrieve the
needed info.
startDrag(self):
    # self is the QListView that starts the drag
    source = self.selectedItem()
    text = source.text(1)   # get the source unique identifier
    dragObj = QTextDrag(text, self) # encode the info
    dragObj.dragMove() # start the drag

dropped(self, e):
    # self is the target QListViewItem
    listview = self.listView()
    text = QString()
    QTextDrag.decode(e, text)
    source = listview.findItem(text,1)
    self.insertItem(source)
    del source

c) dont't encode/decode anything. Because the source remains selected
during the drag selectedItem() is all we need, and both methods become
simpler.
"""
__docformat__ = 'restructuredtext'

import qt

import treeView

class TreeNode(qt.QListViewItem):
    """
    Customized `QListViewItem` that can accept drag and drop events.

    If a given `TreeNode` instance accepts or not drag/drop events depends
    on several factors: the opening mode of the database, the node being
    or not the root node and, finally, the kind of node (group or leaf).
    The methods `dragEntered`, `dragLeft`, `acceptDrop` and `dropped`
    seems to be called only if the drag has started with
    `TreeView.startDrag`.
    """


    def __init__(self, dbview, parent, nodename):
        """
        Create a node in the tree viewer.

        The node's parent can be the `TreeView` or another `TreeNode`
        
        :Parameters:

        - `dbview`: the view of the database where this node lives
        - `parent`: the parent of the node being created
        - `nodename`: the label of the first column of the tree view
        """

        qt.QListViewItem.__init__(self, parent, nodename)

        # The VTApp instance
        self.vtapp = self.listView().vtapp

        # The DBView instance where this TreeNode lives
        self.dbview = dbview

        # Setup the in-place renaming capabilities
        if self.getMode() == 'r':
            self.setRenameEnabled(0, 0)
        else:
            self.setRenameEnabled(0, 1)


    def getFilepath(self):
        """The filepath of the database tied to this node."""
        return self.dbview.dbdoc.filepath


    def getMode(self):
        """The opening mode of the database tied to this node."""
        return self.dbview.dbdoc.mode


    def startRename(self, column):
        """
        Create an editor for in-place renaming.

        If in-place renaming of the item is not enabled then nothing happens.

        :Parameter column: the column being renamed
        """

        if self.getMode() == 'r':
            return
        else:
            qt.QListViewItem.startRename(self, column)


    def okRename(self, column):
        """
        In-place renaming post-processing.

        This function is called if the user presses Enter during
        in-place renaming of the item in column col.

        :Parameter column: the column being renamed
        """

        qt.QListViewItem.okRename(self, column)
        self.listView().emit(qt.PYSIGNAL('itemRenamedInplace(bool)'), (True, ))


    #
    # Drag and Drop related methods
    #
    def setDnD(self, nodetype, is_root=0):
        """
        Setup drag and drop permissions for a given node of the tree view.

        :Parameters:

        - `nodetype`: can be Group or Leaf
        - `mode`: the opening mode of the database
        - `is_root`: can be TRUE or FALSE
        """

        if nodetype == 'Group':
            self.setExpandable(True)
        else:
            self.setExpandable(False)

        if self.getMode() == 'r':
            self.setDragEnabled(1)
            self.setDropEnabled(0)
        else:
            # In append mode drag and drop behavior depends on the kind of node
            if is_root:
                self.setDragEnabled(0)
                self.setDropEnabled(1)
            elif nodetype == 'Group':
                self.setDragEnabled(1)
                self.setDropEnabled(1)
            elif nodetype == 'Leaf':
                self.setDragEnabled(1)
                self.setDropEnabled(0)


    def getDnD(self):
        """
        Description of the drag and drop configuration of the tree view item.

        :Returns:
            a tuple that describes the drag and drop configuration of the item.
        """
        return (self.isExpandable(), self.dragEnabled(), self.dropEnabled())


    def dragEntered(self):
        """A drag has entered the item's bounding rectangle."""

        # When the drag object enters the bounding rectangle of an item
        # the item is made the current item and a marker (a dotted line
        # surrounding the item) is displayed. This way the user can be sure
        # about the current target.
        self.listView().setCurrentItem(self)
        self.repaint()


    def acceptDrop(self, mime_source):
        """
        Accept or reject a drop.

        If the drop is accepted the dropped() method will be called.
        Otherwise nothing will be done.

        :Parameter mime_source: is the data to be decoded by the target
        """

        if self.dropEnabled() and qt.QTextDrag.canDecode(mime_source):
            return 1
        else:
            return 0


    def dropped(self, event):
        """
        Handles dropped events.

        This handler manages the item moving from source to target.

        :Parameter event:
            an event that contains all the information about the drop
        """

        # The listView to which source and target belong
        tree_view = self.listView()

        # Retrieve the source
        data = qt.QString()
        decode = qt.QTextDrag.decode(qt.qApp.clipboard().data(), data)
        if decode:
            data = data.latin1()
            src_filepath, src_nodepath = data.split('#@#')
            source = treeView.findTreeItem(tree_view, src_filepath, src_nodepath)
        else:
            return
        target = self

        # e.action() is always QDropEvent.Copy (I don't know why) so the
        # opening mode is used to decide the kind of requested operation
        if source.getMode() == 'r':
            self.vtapp.slotNodePaste(target)
        else:
            self.vtapp.dropNode(source, target)


    def paintCell(self, painter, colorgr, col, width, align):
        """
        Paint the contents of one column of the item.

        :Parameters:

        - `painter`: the used painter
        - `colorgr`: the used color group
        - `col`: the column being painted
        - `width`: the width of the column
        - `align`: sets how the content is aligned
        """

        if self.isSelected():
            if self.listView().hasFocus():
                colorgr.setColor(qt.QColorGroup.Highlight,
                    qt.QColor(103, 141, 178))
            else:
                colorgr.setColor(qt.QColorGroup.Highlight,
                    qt.QColor(165, 210, 220))
        qt.QListViewItem.paintCell(self, painter, colorgr, col, width, align)
        # The default state of the color group must be restored. If not
        # views titlebars and selected menu items will use the customised
        # color (Qt bug?).
        colorgr.setColor(qt.QColorGroup.Highlight, qt.QColor(103, 141, 178))
