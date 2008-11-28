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
#       $Id: treeView.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the treeview module.

Classes:

* TreeView(qt.QListView)

Methods:

* __init__(self, hspliter, vtapp)
* __tr(self, source, comment=None)
* keyPressEvent(self, event)
* focusInEvent(self, event)
* focusOutEvent(self, event)
* contentsDragEnterEvent(self, event) 
* contentsDragMoveEvent(self, event) 
* contentsDropEvent(self, event)
* encodeNode(self, filepath, nodepath)
* startDrag(self)

Functions:

* flatLVIterator(parent)
* deepLVIterator(parent)
* findTreeItem(tree_view, root_id, nodepath)

Misc variables:

* __docformat__

This module defines the classes used in the creation of a `QListView`
(tree pane) with drag and drop cappabilities. List view items represent nodes
of the database object tree.
"""
__docformat__ = 'restructuredtext'

import tables.path
import qt

import vitables.utils

#
# Tree view related functions
#

def flatLVIterator(parent):
    """
    First level iterator for the tree view.

    :Parameter parent:
        the point where iteration starts. It can be the list view itself
        or a list view item.
    """

    current = parent.firstChild()
    while current:
        yield current
        current = current.nextSibling()


def deepLVIterator(parent):
    """
    Iterate over the whole tree below parent.

    QListView and QListViewItems are no iterable objects, so they
    members cannot be retrieved using a for loop... unless we use
    generators to transform them in iterators.

    :Parameter parent:
        the point where iteration starts. It can be the list view itself
        or a list view item.
    """

    child = parent.firstChild()
    while child:
        yield child
        for item in deepLVIterator(child):
            yield item
        child = child.nextSibling()


def findTreeItem(tree_view, root_id, nodepath):
    """
    Find an item in the tree pane.

    The searched item is univoquely defined in the tree view by
    its top level parent and by its node full path.

    :Parameters:

    - `tree_view`: the tree view pane instance.
    - `root_id`: the ID of the top level parent of the searched item
    - `nodepath`: the full path of the node mapped to the item
    """

    item = None
    # The QListViewItem is located in three steps
    # 1) Traverse the tree to locate the root from which the source hangs
    for child in flatLVIterator(tree_view):
        item_id = child.getFilepath()
        if item_id == root_id:
            top = child
            break

    # 2) Check if the looked for item is a root node
    if top.where == nodepath:
        item = top
        return item

    # 3) Traverse the root hierarchy to locate the source
    for child in deepLVIterator(top):
        path = child.where
        if path == nodepath:
            item = child
            break

    return item


class TreeView(qt.QListView):
    """
    Customized `QListView` that accepts drag and drop events.

    Enabling drag and drop in a list view is not trivial, modifications
    are needed in the list view itself (reimplementing at least `startDrag`
    or `dragObject` method), the viewport (must accept drops) and the list
    view items (must accept drag and/or drops and need reimplement some methods)
    """


    def __init__(self, hspliter, vtapp):
        """
        :Parameters:

        - `vtapp`: an instance of `VTApp`
        - `hspliter`: the parent of the `TreeView` (a `QSplitter` instance)
        """

        qt.QListView.__init__(self, hspliter)
        self.setRootIsDecorated(1)
        self.setSelectionMode(qt.QListView.Single)
        self.setResizeMode(qt.QListView.AllColumns)
        self.setLineWidth(1)
        self.default_frame = self.frameStyle()

        self.vtapp = vtapp

        # Enable drag and drop
        self.viewport().setAcceptDrops(1)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('TreeView', source, comment).latin1()


    def keyPressEvent(self, event):
        """
        Open/close tree nodes.

        If the selected node is a closed leaf it can be opened by
        pressing the plus key. If the selected node is an opened
        it can be closed by pressing the minus key. This way there
        is a complete analogy with the group nodes behavior.

        :Parameter event: a key press event
        """

        selected_node = self.selectedItem()
        if selected_node and selected_node.isExpandable() == False:
            # The key of the leaf in the tracking leaves dictionary
            filepath = selected_node.getFilepath()
            view = self.vtapp.leavesManager.getLeafView(filepath,
                selected_node.where)
            # If the node is opened then close it by pressing the Escape key
            if view and event.key() == qt.Qt.Key_Escape:
                self.vtapp.slotNodeClose(selected_node)
            # If the node is closed then open it by pressing the key
            # Return or Enter
            elif not view and event.key() in [qt.Qt.Key_Return,
                qt.Qt.Key_Enter]:
                self.vtapp.slotNodeOpen(selected_node)
            else:
                qt.QListView.keyPressEvent(self, event)
        else:
            qt.QListView.keyPressEvent(self, event)


    def focusInEvent(self, event):
        """Update the focus indicator."""

        self.setLineWidth(1)
        self.setFrameStyle(qt.QFrame.StyledPanel|qt.QFrame.Plain)
        pal = self.palette()
        pal.setColor(qt.QColorGroup.Foreground, qt.Qt.darkBlue)
        self.setPalette(pal)
        qt.QListView.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Update the focus indicator."""

        self.setFrameStyle(self.default_frame)
        self.setLineWidth(1)
        qt.QListView.focusOutEvent(self, event)


    def contentsDragEnterEvent(self, event) :
        """
        Event handler for `QDragEnterEvent` events.

        Dragging files into the tree pane is accepted. Dragging nodes
        is handled through the `QListView` event handler.
        """

        if qt.QUriDrag.canDecode(event):
            event.accept()
        else:
            qt.QListView.contentsDragEnterEvent(self, event)


    def contentsDragMoveEvent(self, event) :
        """
        Event handler for `QDragMoveEvent` events.

        Moving files into the tree pane is accepted. Moving nodes
        is handled through the `QListView` event handler.
        """

        if qt.QUriDrag.canDecode(event):
            i = self.itemAt(self.contentsToViewport(event.pos()))
            if not i:
                event.accept()
            else:
                # Files cannot be dropped on a tree item
                event.ignore()
        else:
            qt.QListView.contentsDragMoveEvent(self, event)


    def contentsDropEvent(self, event):
        """
        Event handler for QDropEvent events.

        The dropped files are automatically opened.
        """

        if qt.QUriDrag.canDecode(event):
            files_list = qt.QStringList()
            if qt.QUriDrag.decodeLocalFiles(event, files_list):
                event.accept()
                for filename in files_list:
                    self.vtapp.slotFileOpen(filename)
            else:
                event.ignore()
        else:
            qt.QListView.contentsDropEvent(self, event)


    def encodeNode(self, filepath, nodepath):
        """
        Copy the selected node to the XWindow clipboard.

        :Parameters:

        - `filepath`:
            the full path of the database where the node being
            copied/dragged lives
        - `nodepath`: the full path of the node being copied/dragged
        """

        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))

        try:
            # Encode the selected node info.
            # The drag source is the tree view pane. The encoded info
            # looks like /path/to/file.h5#@#/path/to/node
            key = '%s#@#%s' % (filepath, nodepath)
            encoded_obj = qt.QTextDrag(key, self.viewport())
            # Copy the encoded info to the XWindow clipboard
            qt.qApp.clipboard().setData(encoded_obj)
        finally:
            qt.qApp.restoreOverrideCursor()
        return encoded_obj


    def startDrag(self):
        """
        Start a drag operation.

        The drag source is the viewport. When the user starts dragging a
        draggable item in the viewport, this method inits the drag process.
        If the item is not draggable then nothing happens.
        """

	dragged_item = self.selectedItem()
	self.setSelected(dragged_item, False)
	self.repaint()
        # Extract info from the item being dragged and encode it
        # The encoded info looks like /path/to/file.h5#@#path/to/node
        encoded_obj = self.vtapp.slotNodeCopy(dragged_item)
        encoded_obj.dragMove()


