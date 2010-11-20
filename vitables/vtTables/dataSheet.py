# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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
Here is defined the DataSheet class.

Classes:

* DataSheet(QMdiSubWindow)

Methods:

* __init__(self, leaf, view, pindex, parent=None)
* closeEvent(self)
* syncTreeView(self) 

Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

from PyQt4 import QtCore, QtGui

import vitables.utils
import vitables.nodeProperties.nodeInfo as nodeInfo
import vitables.vtWidgets.zoomCell as zoomCell
import vitables.vtTables.leafModel as leafModel
import vitables.vtTables.leafView as leafView
import vitables.vtTables.buffer as readBuffer

class DataSheet(QtGui.QMdiSubWindow):
    """
    The widget containing the displayed data of a given dataset.
    """

    def __init__(self, index, parent=None):
        """Display a given dataset in the MDI area.

        :Parameters:

            - `index`: the index of the displayed *tree* model item
            - `parent`: the parent of the widget
        """

        # The main application window
        self.vtgui = vitables.utils.getVTApp().gui

        # The LeafNode instance whose dataset is being displayed
        dbt_model = self.vtgui.dbs_tree_model
        self.dbt_leaf = dbt_model.nodeFromIndex(index)
        leaf = self.dbt_leaf.node
        rbuffer = readBuffer.Buffer(leaf)
        leaf_model = leafModel.LeafModel(rbuffer)
        leaf_view = leafView.LeafView(leaf_model)

        QtGui.QMdiSubWindow.__init__(self, self.vtgui.workspace)
        self.setWidget(leaf_view)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Customise the title bar
        if not isinstance(leaf.title, unicode):
            title = unicode(leaf.title, 'utf_8')
        else:
            title = leaf.title
        wtitle = u"%s\t%s" % (self.dbt_leaf.name, title)
        self.setWindowTitle(wtitle)
        self.setWindowIcon(self.dbt_leaf.icon)

        # Eventually update the Node menu actions
        self.dbt_leaf.has_view = True
        self.vtgui.updateActions()

        self.pindex = QtCore.QPersistentModelIndex(index)

        # Connect signals to slots
        self.aboutToActivate.connect(self.syncTreeView)
        leaf_view.doubleClicked.connect(self.zoomCell)


    def closeEvent(self, event):
        """Close the window cleanly with the close button of the title bar."""

        # Ensure that Node menu actions are properly updated
        self.dbt_leaf.has_view = False
        self.vtgui.updateActions()

        # Clean up things
        del self.dbt_leaf
        del self.pindex

        # Propagate the event. In the process, self.widget().closeEvent
        # will be called 
        QtGui.QMdiSubWindow.closeEvent(self, event)


    def syncTreeView(self):
        """When the view becomes active select its leaf in the tree view.

        See bug 016548 in the issues tracker for further information on
        this method.
        """

        # Locate the tree view leaf tied to this data sheet. Persistent
        # indices are used to get direct access to the leaf so we don't
        # have to walk the tree
        focus_widget = QtGui.qApp.focusWidget()
        if isinstance(focus_widget, leafView.LeafView):
            self.vtgui.dbs_tree_view.setCurrentIndex(\
                QtCore.QModelIndex(self.pindex))


    def zoomCell(self, index):
        """Display the inner dimensions of a cell.

        :Parameter index: the *leaf* model index of the cell being zoomed
        """

        row = index.row()
        column = index.column()
        tmodel = index.model()
        data = tmodel.rbuffer.getCell(tmodel.rbuffer.start + row, column)

        # The title of the zoomed view
        node = self.dbt_leaf
        info = nodeInfo.NodeInfo(node)
        if node.node_kind == 'table':
            col = info.columns_names[column]
            title = '%s: %s[%s]' % (node.name, col, 
                tmodel.rbuffer.start + row + 1)
        else:
            title = '%s: (%s,%s)' % (node.name, 
                tmodel.rbuffer.start + row + 1, column + 1)

        zoomCell.ZoomCell(data, title, self.vtgui.workspace, 
                          self.dbt_leaf)
