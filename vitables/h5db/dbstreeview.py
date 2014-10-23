#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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
This module defines a view for the tree of databases model.

This view is used to display the tree of open databases. Each top level
node of the tree contains the object tree of a `PyTables`/`HDF5` database.
"""

__docformat__ = 'restructuredtext'

from PyQt4 import QtCore
from PyQt4 import QtGui


from vitables.h5db.nodeitemdelegate import NodeItemDelegate


translate = QtGui.QApplication.translate


class DBsTreeView(QtGui.QTreeView):
    """
    A view for the databases tree model.

    :Parameters:
        - `vtapp`: the VTAPP instance
        - `model`: the model for this view
    """


    dbsTreeViewCreated = QtCore.pyqtSignal(QtGui.QTreeView)

    def __init__(self, vtapp, model):
        """Create the view.
        """

        super(DBsTreeView, self).__init__(parent=None)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.vtapp = vtapp
        self.vtgui = self.vtapp.gui

        # The model
        self.setModel(model)
        self.dbt_model = model
        self.smodel = self.selectionModel()

        # The custom delegate used for editing items
        self.setItemDelegate(NodeItemDelegate(self))
        self.setObjectName('dbs_tree_view')

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QtGui.QPalette.Active,
                QtGui.QPalette.WindowText)}

        # Setup drag and drop
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        # Misc. setup
        self.setRootIsDecorated(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setWhatsThis(translate('DBsTreeView',
            """<qt>
            <h3>The Tree of databases</h3>
            For every open database this widget shows the object tree,
            a graphical representation<br>of the data hierarchy stored
            in the database.</qt>""",
            'WhatsThis help for the tree pane'))

        # Connect signals to slots
        self.customContextMenuRequested.connect(self.createCustomContextMenu)
        self.activated.connect(self.activateNode)
        self.expanded.connect(self.updateExpandedGroup)
        self.collapsed.connect(self.updateCollapsedGroup)
        self.dbt_model.layoutChanged.connect(self.updateColumnWidth)
    #    self.dbsTreeViewCreated.connect(self.vtgui.setup)

    #    self.dbsTreeViewCreated.emit(self)
        self.vtgui.setup(self)


    def updateColumnWidth(self):
        """Make sure that a horizontal scrollbar is shown as needed.

        This is a subtle method. As the tree view has only 1 column its
        width and the width of the viewport are always the same so the
        horizontal scrollbar is never shown. As the contents width
        changes every time the layout changes (rows are inserted or
        deleted) by resizing column to contents when it happens we
        ensure that the column and the viewport will have different
        width and the scrollbar will indeed be added as needed.
        """
        self.resizeColumnToContents(0)


    def activateNode(self, index):
        """Expand an item via `Enter`/`Return` key or mouse double click.

        When the user activates a collapsed item (by pressing `Enter`, `Return`
        or by double clicking the item) then it is expanded. If the user
        activates the node by double clicking on it while the `Shift` key is
        pressed, the item is edited (if editing is enabled).

        Lazy population of the model is partially implemented in this
        method. Expanded items are updated so that children items are added if
        needed. This fact improves enormously the performance when files
        whit a large number of nodes are opened.

        This method is a slot connected to the activated(QModelIndex) signal
        in the ctor.

        :Parameter index: the index of the activated item
        """

        node = self.dbt_model.nodeFromIndex(index)
        if node.node_kind.count('group'):
            if not self.isExpanded(index):
                self.expand(index)
        elif not node.has_view:
            self.vtapp.nodeOpen(index)


    def updateCollapsedGroup(self, index):
        """After collapsing a group update its icon.

        This method is a slot connected to the `collapsed(QModelIndex)` signal
        in the ctor.

        :Parameter index: the index of the collapsed group
        """

        node = self.dbt_model.nodeFromIndex(index)
        if node.node_kind == 'group':
            self.dbt_model.setData(index, node.closed_folder,
                QtCore.Qt.DecorationRole)
        self.smodel.clearSelection()
        self.smodel.setCurrentIndex(index,
            QtGui.QItemSelectionModel.SelectCurrent)
        self.update(index)


    def updateExpandedGroup(self, index):
        """After a group expansion, update the icon and the displayed children.

        Lazy population of the model is partially implemented in this
        method. Expanded items are updated so that children items are added if
        needed. This fact reduces enormously the opening times for files
        whit a large number of nodes and also saves memory.

        This method is a slot connected to the `expanded(QModelIndex)` signal
        in the ctor.

        :Parameter index: the index of the expanded item
        """

        node = self.dbt_model.nodeFromIndex(index)
        node_kind = node.node_kind
        if node_kind == 'group':
            self.dbt_model.setData(index, node.open_folder,
                QtCore.Qt.DecorationRole)
        if node_kind in ['group', 'root group']:
            if not node.updated:
                self.dbt_model.lazyAddChildren(index)
                node.updated = True
                self.smodel.clearSelection()
                self.smodel.setCurrentIndex(index,
                    QtGui.QItemSelectionModel.SelectCurrent)


    def createCustomContextMenu(self, pos):
        """
        A context menu for the tree of databases view.

        When an item of the tree view is right clicked, a context popup
        menu is displayed. The content of the popup depends on the
        clicked element.

        :Parameter pos: the local position at which the menu will popup
        """

        index = self.indexAt(pos)
        if not index.isValid():
            kind = 'view'
        else:
            node = self.dbt_model.nodeFromIndex(index)
            kind = node.node_kind
        pos = self.mapToGlobal(pos)
        self.vtgui.popupContextMenu(kind, pos)


    def currentChanged(self, current, previous):
        """This slot is automatically called when the current item changes.

        The slot is not called if the item doesn't actually changed.
        When the current item changes the menus, toolbars and statusbar have
        to be updated. Probably some QActions will be enabled and other will
        be disabled. Also the databases tree and the workspace have to be
        synchronised again (if possible).

        :Parameters:

          - `current`: the index model of the new current item
          - `previous`: the index model of the previous current item
        """

        QtGui.QTreeView.currentChanged(self, current, previous)
        self.vtgui.updateActions()
        self.vtgui.updateStatusBar()

        # Sync the tree view with the workspace (if needed) but keep the
        # focus (giving focus to the workspace when a given item is
        # selected is counter intuitive)
        pcurrent = QtCore.QPersistentModelIndex(current)
        for window in self.vtgui.workspace.subWindowList():
            if pcurrent == window.pindex:
                self.vtgui.workspace.setActiveSubWindow(window)
                self.setFocus(True)


    def selectNode(self, index):
        """Select the given index.

        :Parameters `index`: the model index being selected
        """

        self.smodel.clearSelection()
        self.smodel.setCurrentIndex(index,
            QtGui.QItemSelectionModel.SelectCurrent)


    def mouseDoubleClickEvent(self, event):
        """Specialised handler for mouse double click events.

        When a node is double clicked in the tree of databases pane:

        - if the node can be renamed and the `Shift` key is pressed then
          rename the node
        - if the node is a leaf with no view and the `Shift` key is not pressed
          then open the node
        - if the node is a collpased group and the `Shift` key is not pressed
          then expand the group

        :Parameter event: the event being processed

        """

        modifier = event.modifiers()
        current = self.currentIndex()
        if modifier == QtCore.Qt.ShiftModifier:
            if current.flags() & QtCore.Qt.ItemIsEditable:
                self.edit(current)
        else:
            self.activateNode(current)


    def dropEvent(self, event):
        """
        Event handler for `QDropEvent` events.

        If an icon is dropped on a free area of the tree view then the
        icon URL is converted to a path (which we assume to be an `HDF5`
        file path) and ``ViTables`` tries to open it.

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        if mime_data.hasFormat('text/uri-list'):
            if self.dbt_model.dropMimeData(\
                mime_data, QtCore.Qt.CopyAction, -1, -1, self.currentIndex()):
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
                self.setFocus(True)
        else:
            QtGui.QTreeView.dropEvent(self, event)


    def dragEnterEvent(self, event):
        """
        Event handler for `QDragEnterEvent` events.

        Dragging files from the Desktop onto the tree view is supported.

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

        Dragging files from the Desktop onto the tree view is supported. If the
        icon being dragged is placed over a tree view item then drop operations
        are not allowed (dragging icon is a slashed circle).

        :Parameter event: the event being processed.
        """

        mime_data = event.mimeData()
        if mime_data.hasFormat('text/uri-list'):
            event.setDropAction(QtCore.Qt.CopyAction)
            event.acceptProposedAction()
        else:
            return QtGui.QTreeView.dragMoveEvent(self, event)


    def focusInEvent(self, event):
        """Specialised handler for focus events.

        Repaint differently the databases tree view frame when it gets the
        keyboard focus so that users can realize easily about this focus
        change.

        :Parameter event: the event being processed
        """

        self.setLineWidth(2)
        self.setFrameStyle(QtGui.QFrame.Panel|QtGui.QFrame.Plain)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText,
            QtCore.Qt.darkBlue)
        QtGui.QTreeView.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Specialised handler for focus events.

        Repaint differently the databases tree view frame when it looses the
        keyboard focus so that users can realize easily about this focus
        change.

        :Parameter event: the event being processed
        """

        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText,
            self.frame_style['foreground'])
        QtGui.QTreeView.focusOutEvent(self, event)

if __name__ == '__main__':
    import sys
    APP = QtGui.QApplication(sys.argv)
    TREE = DBsTreeView()
    TREE.show()
    APP.exec_()
