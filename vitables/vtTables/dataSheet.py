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
#       $Id: dataSheet.py 1081 2008-10-24 17:53:26Z vmas $
#
########################################################################

"""
Here is defined the DataSheet class.

Classes:

* DataSheet(QtGui.QMdiSubWindow)

Methods:


Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

class DataSheet(QtGui.QMdiSubWindow):
    """
    The widget containing the displayed data of a given dataset.
    """

    def __init__(self, leaf, view, pindex, parent=None):
        """Display a given dataset in the MDI area.

        :Parameters:

            - `leaf`: the LeafNode instance whose dataset is being displayed
            - `view`: the displayed LeafView instance
            - `pindex`: a persistent model index
            - `parent`: the parent of the widget
        """

        QtGui.QMdiSubWindow.__init__(self, parent)
        view.data_sheet = self
        self.setWidget(view)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # The main application window
        self.vtapp = parent

        # The persistent index of the tree of databases node whose
        # dataset is being displayed here
        self.pindex = pindex

        # Take advantage of the MDI area capabilities for locating the nodes
        # currently displayed (see for instance VTApp.slotFileClose)
        self.leaf = leaf

        # Customise the title bar
        title = u"%s\t%s" % (leaf.name, leaf.node.title)
        self.setWindowTitle(title)
        self.setWindowIcon(leaf.icon)

        # Eventually update the Node menu actions
        leaf.has_view = True
        self.vtapp.slotUpdateActions()

        self.connect(self, QtCore.SIGNAL("aboutToActivate()"), 
                     self.syncTreeView)


    def closeEvent(self, event):
        """Close the window cleanly with the close button of the title bar."""

        # Ensure that Node menu actions are properly updated
        self.leaf.has_view = False
        self.vtapp.slotUpdateActions()
        QtGui.QMdiSubWindow.closeEvent(self, event)


    def syncTreeView(self):
        """When the view becomes active select its leaf in the tree view.
        """

        index_list = self.vtapp.dbs_tree_model.persistentIndexList()
        for index in index_list:
            if index == self.pindex:
                self.vtapp.dbs_tree_view.setCurrentIndex(index)

