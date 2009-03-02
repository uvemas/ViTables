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
Here is defined the DBsTreeView class.

Classes:

* DBsTreeView(QTreeView)

Methods:

* __init__(self, vtapp, parent=None)
* __tr(self, source, comment=None)
* mouseDoubleClickEvent(self, event)
* updateCollapsedGroup(self, index)
* updateExpandedGroup(self, index)
* activateNode(self, index)
* createCustomContextMenu(self, pos)
* currentChanged(self, current, previous)
* dropEvent(self, event)
* dragEnterEvent(self, event)
* dragMoveEvent(self, event)

Functions:


Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'DBsTreeView'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from vitables.h5db.nodeItemDelegate import NodeItemDelegate

class DBsTreeView(QTreeView):
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

        QTreeView.__init__(self, parent)
        self.vtapp = vtapp

        # The custom delegate used for editing items
        self.setItemDelegate(NodeItemDelegate(self))
        self.setObjectName('dbs_tree_view')

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QPalette.Active, 
                QPalette.WindowText)}

        # Setup drag and drop
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # Misc. setup
        self.setRootIsDecorated(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setWhatsThis(self.__tr(
            """<qt>
            <h3>The Tree of databases</h3>
            For every open database this widget shows the object tree, 
            a graphical representation<br>of the data hierarchy stored
            in the database.</qt>""",
            'WhatsThis help for the tree pane'))

        # Connect signals to slots
        self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"),
            self.createCustomContextMenu)
        self.connect(self, SIGNAL('activated(QModelIndex)'),
            self.activateNode)
        self.connect(self, SIGNAL('expanded(QModelIndex)'),
            self.updateExpandedGroup)
        self.connect(self, SIGNAL('collapsed(QModelIndex)'),
            self.updateCollapsedGroup)


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


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
        if modifier == Qt.ShiftModifier:
            if current.flags() & Qt.ItemIsEditable:
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
            model.setData(index, QVariant(node.closed_folder),
                Qt.DecorationRole)

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
            model.setData(index, QVariant(node.open_folder),
                Qt.DecorationRole)
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
        pcurrent = QPersistentModelIndex(current)
        for window in self.vtapp.workspace.subWindowList():
            if pcurrent == window.pindex:
                self.vtapp.workspace.setActiveSubWindow(window)

        QTreeView.currentChanged(self, current, previous)
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
            if model.dropMimeData(mime_data, Qt.CopyAction, -1, -1, 
                self.currentIndex()):
                event.setDropAction(Qt.CopyAction)
                event.accept()
        else:
            QTreeView.dropEvent(self, event)
    def dragEnterEvent(self, event):
        """
        Event handler for `QDragEnterEvent` events.

        Dragging files on the tree view is supported.

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        if mime_data.hasFormat('text/uri-list'):
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()
        else:
            QTreeView.dragEnterEvent(self, event)
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
            event.setDropAction(Qt.CopyAction)
            event.acceptProposedAction()
        else:
            return QTreeView.dragMoveEvent(self, event)


    def focusInEvent(self, event):
        """Specialised handler for focus events.

        :Parameter event: the event being processed
        """

        self.setLineWidth(2)
        self.setFrameStyle(QFrame.Panel|QFrame.Plain)
        pal = self.palette()
        pal.setColor(QPalette.Active, QPalette.WindowText, Qt.darkBlue)
        QTreeView.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Specialised handler for focus events.

        :Parameter event: the event being processed
        """

        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        pal = self.palette()
        pal.setColor(QPalette.Active, QPalette.WindowText, 
            self.frame_style['foreground'])
        QTreeView.focusOutEvent(self, event)

if __name__ == '__main__':
    import sys
    APP = QApplication(sys.argv)
    TREE = DBsTreeView()
    TREE.show()
    APP.exec_()
