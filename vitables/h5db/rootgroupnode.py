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
This module defines a data structure to be used for the model of the databases
tree. The data structure is equivalent to a root group node in a `PyTables`
file.
"""

__docformat__ = 'restructuredtext'

import vitables.utils
from vitables.h5db import tnode_editor
from vitables.nodeprops import nodeinfo
from vitables.nodeprops import grouppropdlg

class RootGroupNode(object):
    """
    A root group node in the tree of databases model.

    Root group nodes are top level nodes (i.e., they have no parent).

    :Parameters:

    - `data_source`: the data source of the node.
    - `parent`: the parent of the node.
    - `tmp_db`: True if the node is tied to the temporary database
    """

    def __init__(self, model, data_source=None, parent=None, tmp_db=False):
        """Create the root group node for the tree of databases model.

        The root of the tree of databases model is a RootGroupNode with
        no parent and no data source. Any other RootGroupNode represents
        a root group of a HDF5 file and has a parent (the root of the
        tree of databases model) and a data source (the HDF5 file).
        """

        self.dbt_model = model
        self.updated = False
        self.children = []
        self.parent = parent
        self.name = 'root node'
        self.filepath = None
        self.node_kind = 'root group'
        if data_source:
            self.node = data_source.get_node('/')

            self.has_view = False

            # Attributes that the tree of databases view will use
            # name --> DisplayRole
            # nodepath --> ToolTipRole
            # as_record --> StatusTipRole
            # icon --> DecorationRole
            if tmp_db:
                self.name = 'Query results'
            else:
                self.name = data_source.filename
            self.nodepath = '/'
            self.filepath = data_source.filepath
            self.as_record = '{0}->{1}'.format(self.filepath, self.nodepath)
            self.mode = data_source.mode
            icons = vitables.utils.getIcons()
            if tmp_db:
                self.icon = icons['dbfilters']
            elif self.mode == 'r':
                self.icon = icons['file_ro']
            else:
                self.icon = icons['file_rw']


    def __len__(self):
        """The number of children of this grup."""
        return len(self.children)


    def insertChild(self, child, position=0):
        """Insert a child in a group node.

        :Parameters:

            - `child`: the node being inserted
            - `position`: the insertion position
        """
        self.children.insert(position, child)


    def childAtRow(self, row):
        """The row-th child of this node.

        :Parameter row: the position of the retrieved child
        """

        assert 0 <= row <= len(self.children)
        return self.children[row]


    def rowOfChild(self, child):
        """The row index of a given child.

        :Parameter child: the child node whose position is being retrieved.
        """

        for pos, node in enumerate(self.children):
            if node == child:
                return pos
        return -1


    def row(self):
        """The position of this node in the parent's list of children.
        """

        if self.parent:
            return self.parent.children.index(self)

        return 0


    def findChild(self, childname):
        """The child node with a given name.

        :Parameter childname: the name of the wanted child node.
        """

        for node in self.children:
            if node.name == childname:
                return node
        return None


    def editor(self):
        """Return an instance of `TNodeEditor`.
        """
        return tnode_editor.TNodeEditor(self.dbt_model.getDBDoc(self.filepath))


    def properties(self):
        """The Properties dialog for this node.
        """

        info = nodeinfo.NodeInfo(self)
        grouppropdlg.GroupPropDlg(info)
