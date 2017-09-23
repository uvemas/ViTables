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
This module defines a widget that wraps the view widget of leaves.

When a leaf node is opened in the tree of databases view the data stored in
that leaf will be displayed in the workspace using this wrapper widget.
"""

from qtpy import QtCore
from qtpy import QtWidgets

from . import leaf_view, leaf_model, df_model
from .. import utils as vtutils
from ..nodeprops import nodeinfo
from ..vtwidgets import zoom_cell

__docformat__ = 'restructuredtext'


class DataSheet(QtWidgets.QMdiSubWindow):
    """
    The widget containing the displayed data of a given dataset.

    :Parameter index: the index (in the tree of databases model) of the leaf
      whose data will be displayed
    """

    def __init__(self, index):
        """Display a given dataset in the MDI area.
        """

        # The main application window
        self.vtgui = vtutils.getVTApp().gui

        # The data structure (LeafNode/LinkNode instance) whose dataset
        # is being displayed
        dbt_model = self.vtgui.dbs_tree_model
        self.dbt_leaf = dbt_model.nodeFromIndex(index)

        # The tables.Node instance tied to that data structure
        pt_node = self.dbt_leaf.node
        if hasattr(pt_node, 'target'):
            # The selected item is a link and must be dereferenced
            leaf = pt_node()
        else:
            leaf = pt_node

        self.leaf_model = df_model.try_opening_as_dataframe(leaf)
        if not self.leaf_model:
            self.leaf_model = leaf_model.LeafModel(leaf)

        self.leaf_view = leaf_view.LeafView(self.leaf_model)

        super(DataSheet, self).__init__(self.vtgui.workspace,
                                        QtCore.Qt.SubWindow)
        self.setWidget(self.leaf_view)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Customize the title bar
        if not isinstance(leaf.title, str):
            title = str(leaf.title)
        else:
            title = leaf.title
        wtitle = "{0}\t{1}".format(self.dbt_leaf.name, title)
        self.setWindowTitle(wtitle)
        self.setWindowIcon(self.dbt_leaf.icon)

        # Eventually update the Node menu actions
        self.dbt_leaf.has_view = True
        self.vtgui.updateActions()

        self.pindex = QtCore.QPersistentModelIndex(index)

        # Connect signals to slots
        self.aboutToActivate.connect(self.syncTreeView)
        self.leaf_view.doubleClicked.connect(self.zoomCell)

    def closeEvent(self, event):
        """Close the window cleanly with the close button of the title bar.

        :Parameter event: the event being processed
        """

        # Ensure that Node menu actions are properly updated
        self.dbt_leaf.has_view = False
        self.vtgui.updateActions()

        # Propagate the event. In the process, self.widget().closeEvent
        # will be called
        QtWidgets.QMdiSubWindow.closeEvent(self, event)

        if not self.vtgui.workspace.subWindowList():
            self.vtgui.dbs_tree_view.setFocus(True)

    def focusInEvent(self, event):
        """Specialised handler for focus events.

        Synchronize with the tree view when the view gets keyboard focus.

        :Parameter event: the event being processed
        """

        # Sync the workspace with the tree view (if needed) but keep the
        # focus (giving focus to the tree view when a given view is
        # clicked is counter intuitive)
        QtWidgets.QMdiSubWindow.focusInEvent(self, event)
        self.syncTreeView()
        self.setFocus(True)

    def syncTreeView(self):
        """
        If the view is activated select its leaf in the tree of databases view.
        """

        if self.vtgui.editing_dlg is not None:
            self.vtgui.editing_dlg = None
            return
        # Locate the tree view leaf tied to this data sheet. Persistent
        # indices are used to get direct access to the leaf so we don't
        # have to walk the tree
        self.vtgui.dbs_tree_view.setCurrentIndex(
            QtCore.QModelIndex(self.pindex))

    def zoomCell(self, index):
        """Display the inner dimensions of a cell.

        :Parameter index: the index (in the leaf model) of the cell being zoomed
        """

        row = index.row()
        column = index.column()
        tmodel = index.model()
        data = tmodel.cell(row, column)
        if data is None:
            return

        # The title of the zoomed view
        node = self.dbt_leaf
        info = nodeinfo.NodeInfo(node)
        if node.node_kind == 'table':
            col = info.columns_names[column]
            title = '{0}: {1}[{2}]'.format(node.name, col,
                                           tmodel.start + row)
        else:
            title = '{0}: ({1},{2})'.format(node.name,
                                            tmodel.start + row, column)

        zoom_cell.ZoomCell(data, title, self.vtgui.workspace,
                           self.dbt_leaf)
