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
#       $Id: nodeDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the NodeDoc class.

Classes:

* NodeDoc(qt.QObject)

Methods:

* __init__(self, dbdoc, nodepath)
* isInstanceOf(self, *class_names)
* getASI(self)
* getNodeAttributes(self, kind)
* move(self)
* rename(self, final_path, initial_path)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import tables
import qt

import vitables.utils

class NodeDoc(qt.QObject):
    """
    A data structure that defines a node (group or leaf).

    This class represents the model that is controlled by the leaves
    manager, i.e. an instance of the `tables.File`, `tables.Group` or a
    `tables.Leaf` derived classes. It exposes methods to get node
    metadata.
    """


    def __init__(self, dbdoc, nodepath):
        """
        Creates a document that represents a node (group or leaf).

        :Parameters:

        - `dbdoc`: the database where node lives
        - `nodepath`: the full path of node in the database object tree
        """

        qt.QObject.__init__(self)

        # The attached view
        self.leafview = None

        # The node...
        self.dbdoc = dbdoc
        self.node = self.dbdoc.getNode(nodepath)
        self.filepath = self.dbdoc.filepath
        self.nodepath = nodepath


    def isInstanceOf(self, *class_names):
        """
        Check if the node is an instance of some of the given classes.

        :Parameter classNames: the names of the classes being checked

        :Returns: TRUE if node is an instance of some of the listed classes
        """

        name2class = {'Group': tables.Group, 'Leaf': tables.Leaf,
            'Table': tables.Table, 'Array': tables.Array,
            'CArray': tables.CArray, 'EArray': tables.EArray,
            'VLArray': tables.VLArray, 'UnImplemented': tables.UnImplemented}

        # Default value
        for name in class_names:
            if isinstance(self.node, name2class[name]):
                return True


    def getASI(self):
        """:Returns: the attribute set instance"""

        if isinstance(self.node, tables.Group):
            return self.node._v_attrs
        else:
            return self.node.attrs


    def getNodeAttributes(self, kind):
        """
        Get the user and system attributes for a given node.

        `HDF5` files created with tools other than `PyTables` will not have
        system attributes unless users add them in order to keep fully
        compatibility with `PyTables` format, and may not have user
        attributes. So, not truly native `PyTable` files can return empty
        dictionaries of attributes.

        :Parameter kind:
            the kind of attribute being retrieved. Can be 'system' or 'user'

        :Returns: the system/user attributes dictionary
        """

        # Get the list of user/system attributes
        asi = self.getASI()
        if kind == 'system':
            names = asi._v_attrnamessys
        else:
            names = asi._v_attrnamesuser

        # Make a dictionary of system/user attributes
        return dict((n, getattr(asi, n, None)) for n in names)

    #
    # Editing datasets
    #

    def move(self):
        """Move the selected dataset."""

        # Propagate changes to the attached view
        self.leafview.hp_table.doc = self
        self.leafview.hp_table.hpViewport.doc = self
        # Reset the buffer. This is a MUST!
        self.getBuffer(0,  self.buffer.chunkSize)
        # Large tables (numRows >= maxNumRows) needs a sync
        if self.leafview.hp_table.hpScrollBar.isVisible():
            self.leafview.hp_table.syncTable()
        # Update info button and titlebar
        self.leafview.configTable()
        self.leafview.updateInfoTooltip()
        self.leafview.hp_table.hpViewport.repaintContents()


    def rename(self, final_path, initial_path):
        """
        Rename the selected dataset.

        :Parameters:

        - `final_path`: the node new name
        - `initial_path` the node current name
        """

        self.nodepath = self.nodepath.replace(initial_path, final_path, 1)
        # Propagate changes to the attached view
        self.leafview.configTable()
        self.leafview.updateInfoTooltip()


