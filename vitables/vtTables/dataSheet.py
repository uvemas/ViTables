# -*- coding: utf-8 -*-
#!/usr/bin/env python

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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils
import vitables.nodeProperties.nodeInfo as nodeInfo
import vitables.vtWidgets.zoomCell as zoomCell

class DataSheet(QMdiSubWindow):
    """
    The widget containing the displayed data of a given dataset.
    """

    def __init__(self, view, parent=None):
        """Display a given dataset in the MDI area.

        :Parameters:

            - `view`: the displayed LeafView instance
            - `parent`: the parent of the widget
        """

        # The main application window
        self.vtapp = vitables.utils.getVTApp()

        QMdiSubWindow.__init__(self, self.vtapp.workspace)
        self.setWidget(view)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # The LeafNode instance whose dataset is being displayed
        dbt_view = self.vtapp.dbs_tree_view
        dbt_model = self.vtapp.dbs_tree_model
        index = dbt_view.currentIndex()
        dbt_leaf = dbt_model.nodeFromIndex(index)

        # Customise the title bar
        if not isinstance(dbt_leaf.node.title, unicode):
            title = unicode(dbt_leaf.node.title, 'utf_8')
        else:
            title = dbt_leaf.node.title
        wtitle = u"%s\t%s" % (dbt_leaf.name, title)
        self.setWindowTitle(wtitle)
        self.setWindowIcon(dbt_leaf.icon)

        # Eventually update the Node menu actions
        dbt_leaf.has_view = True
        self.vtapp.slotUpdateActions()

        self.dbt_leaf = dbt_leaf
        self.pindex = QPersistentModelIndex(index)
        self.rbuffer = view.rbuffer

        self.connect(self, SIGNAL("aboutToActivate()"), 
                     self.syncTreeView)
        self.connect(view, SIGNAL("doubleClicked(QModelIndex)"), 
            self.zoomCell)


    def closeEvent(self, event):
        """Close the window cleanly with the close button of the title bar."""

        # Ensure that Node menu actions are properly updated
        self.dbt_leaf.has_view = False
        self.vtapp.slotUpdateActions()
    #    self.setParent(None)
    #    self.vtapp = None
    #    self.rbuffer = None
    #    self.pindex = None
    #    self.dbt_leaf = None
    #    event.accept()
        QMdiSubWindow.closeEvent(self, event)


    def syncTreeView(self):
        """When the view becomes active select its leaf in the tree view.
        """

        # Locate the tree view leaf tied to this data sheet. Persistent
        # indices are used to get direct access to the leaf so we don't
        # have to walk the tree
        self.vtapp.dbs_tree_view.setCurrentIndex(QModelIndex(self.pindex))


    def zoomCell(self, index):
        """Display the inner dimensions of a cell.

        :Parameter index: the model index of the cell being zoomed
        """

        row = index.row()
        column = index.column()
        data = self.rbuffer.getCell(self.rbuffer.start + row, column)

        # The title of the zoomed view
        node = self.dbt_leaf
        info = nodeInfo.NodeInfo(node)
        if node.node_kind == 'table':
            col = info.columns_names[column]
            title = '%s: %s[%s]' % (node.name, col, self.rbuffer.start + row + 1)
        else:
            title = '%s: (%s,%s)' % (node.name, self.rbuffer.start + row + 1, 
                column + 1)

        zoomCell.ZoomCell(data, title, self.vtapp.workspace, 
                          self.dbt_leaf)
