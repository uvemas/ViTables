# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
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
#       $Id: dbsTreeView.py 1080 2008-10-24 10:15:45Z vmas $
#
########################################################################

"""
Here is defined the DBsTreeView class.

Classes:

* DBsTreeView(QtGui.QTreeView)

Methods:

* __init__(self, parent=None)
* __tr(self, source, comment=None)
* activateNode(self, index)
* collapseNode(self, index)
* createCustomContextMenu(self, pos)
* expandNode(self, index)

Functions:


Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import sets

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

from vitables.h5db.nodeItemDelegate import NodeItemDelegate

class DBsTreeView(QtGui.QTreeView):
    """
    The tree of DBs view.
    
    This is one of the views of the tree of databases model.
    This view is used to display the tree of open databases. Each top level
    node of the tree contains the object tree of a database.
    """

    def __init__(self, vtapp, parent=None):
        """Create the view.

        :Parameters:

            - `vtapp`: the application main window
            - `parent`: the parent widget.
        """

        QtGui.QTreeView.__init__(self, parent)
        self.vtapp = vtapp

        # The custom delegate used for editing items
        self.setItemDelegate(NodeItemDelegate(self))
        self.setObjectName('dbs_tree_view')


        # Setup drag and drop
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # Misc. setup
        self.setRootIsDecorated(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setWhatsThis(self.__tr(
            """<qt>
            <h3>The Tree of databases</h3>
            For every open database this widget shows the object tree, 
            a graphical representation<br>of the data hierarchy stored
            in the database.</qt>""",
            'WhatsThis help for the tree pane'))

        # Connect signals to slots
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
            self.createCustomContextMenu)
        self.connect(self, QtCore.SIGNAL('activated(QModelIndex)'),
            self.activateNode)
        self.connect(self, QtCore.SIGNAL('expanded(QModelIndex)'),
            self.updateExpandedGroup)
        self.connect(self, QtCore.SIGNAL('collapsed(QModelIndex)'),
            self.updateCollapsedGroup)


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate('DBsTreeView', source, 
                                            comment).toUtf8(), 'utf_8')


    def mouseDoubleClickEvent(self, event):
        """Specialised handler for mouse double click events.

        When a node is double clicked in the tree of databases pane:
        - if the node can be renamed and the Shift key is pressed then
          rename the node
        - if the node is a leaf with no view and the Shift key is not pressed
          then open the node
        - if the node is a collpased group and the Shift key is not pressed
          then expand the group
        """

        modifier = event.modifiers()
        current = self.currentIndex()
        if modifier == QtCore.Qt.ShiftModifier:
            if current.flags() & QtCore.Qt.ItemIsEditable:
                self.edit(current)
        else:
            self.activateNode(current)


    def updateCollapsedGroup(self, index):
        """After collapsing a group update its icon.

        :Parameter index: the index of the collapsed group
        """

        model = self.model()
        node = model.nodeFromIndex(index)
        if node.node_kind == 'group':
            model.setData(index, QtCore.QVariant(node.closed_folder),
                QtCore.Qt.DecorationRole)


    def updateExpandedGroup(self, index):
        """After a group expansion update the icon and the displayed children.

        Lazy population of the model is partially implemented in this
        method. Expanded items are updated so that children items are added if
        needed. This fact reduces enormously the opening times for files
        whit a large number of nodes and also saves memory.

        :Parameter index: the index of the expanded item
        """

        model = self.model()
        node = model.nodeFromIndex(index)
        node_kind = node.node_kind
        if node_kind in ['group', 'root group']:
            model.lazyAddChildren(index)
        if node_kind == 'group':
            model.setData(index, QtCore.QVariant(node.open_folder),
                QtCore.Qt.DecorationRole)
        self.update(index)


    def activateNode(self, index):
        """Expands/collapses an item.

        When the user activates the item by pressing Enter collapsed
        items are expanded. If the user activates the node by double
        clicking on it, the item is edited (if editing is enabled).

        Lazy population of the model is partially implement in this
        method. Expanded items are updated so that children items are added if
        needed. This fact improves enormously the performance when files
        whit a large number of nodes are opened.

        :Parameter index: the index of the activated item
        """

        model = self.model()
        node = model.nodeFromIndex(index)
        if node.node_kind.count('group'):
            if not self.isExpanded(index):
                self.expand(index)
        elif not node.has_view:
            self.vtapp.slotNodeOpen(index)



    def createCustomContextMenu(self, pos):
        """
        A context menu for the tree of databases view.

        When an item of the tree view is right clicked, a context popup
        menu is displayed. The content of the popup depends on the
        clicked element.

        :Parameter pos: the local position at which the menu will popup
        """

        model = self.model()
        index = self.indexAt(pos)
        if not index.isValid():
            kind = 'view'
        else:
            node = model.nodeFromIndex(index)
            kind = node.node_kind
        pos = self.mapToGlobal(pos)
        self.vtapp.popupContextualMenu(kind, pos)


    def currentChanged(self, current, previous):
        """This slot is automatically called when the current item changes.

        :Parameters:

        -`current`: the index model of the new current item
        -`previous`: the index model of the previous current item
        """

        self.vtapp.slotUpdateActions()
        self.vtapp.updateStatusBar()

        # Activate the view (if any) of the selected node
        pcurrent = QtCore.QPersistentModelIndex(current)
        for window in self.vtapp.workspace.subWindowList():
            if pcurrent == window.pindex:
                self.vtapp.workspace.setActiveSubWindow(window)

        QtGui.QTreeView.currentChanged(self, current, previous)


    def dropEvent(self, event):
        """
        Event handler for `QDropEvent` events.

        If an icon is dropped on a free area of the tree view then the
        icon URL is converted to a path (which we assume to be an HDF5
        file path) and ViTables tries to open it.

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        model = self.model()
        if mime_data.hasFormat('text/uri-list'):
            if model.dropMimeData(mime_data, QtCore.Qt.CopyAction, -1, -1, 
                self.currentIndex()):
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
        else:
            QtGui.QTreeView.dropEvent(self, event)

    def dragEnterEvent(self, event):
        """
        Event handler for `QDragEnterEvent` events.

        Dragging files on the tree view is supported.

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        if mime_data.hasFormat('text/uri-list'):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.acceptProposedAction()
        else:
            QtGui.QTreeView.dragEnterEvent(self, event)


    def dragMoveEvent(self, event):
        """
        Event handler for `QDragMoveEvent` events.

        Dragging files on the tree view is supported. If the icon being
        dragged is placed over a tree view item then drop operations are
        not allowed (dragging icon is a slashed circle).

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        if mime_data.hasFormat('text/uri-list'):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.acceptProposedAction()
        else:
            return QtGui.QTreeView.dragMoveEvent(self, event)




if __name__ == '__main__':
    import sys
    APP = QtGui.QApplication(sys.argv)
    TREE = DBsTreeView()
    TREE.show()
    APP.exec_()

