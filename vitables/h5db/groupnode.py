#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2019 Vicent Mas. All rights reserved
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
tree. The data structure is equivalent to a (non root) group node in a
`PyTables` file.
"""

__docformat__ = 'restructuredtext'

import vitables.utils
from vitables.h5db import tnode_editor
from vitables.nodeprops import nodeinfo
from vitables.nodeprops import grouppropdlg

class GroupNode(object):
    """
    A group node in the tree of databases model.

    :Parameters:

    - `parent`: the parent of the node.
    - `name`: the name of the node
    """

    def __init__(self, model, parent, name):
        """Create a group node for the tree of databases model.

        A GroupNode represents a (non root) group of a `HDF5` file and has
        a parent (another group node of the tree of databases model) and
        a name.
        """

        self.dbt_model = model
        self.updated = False
        self.children = []
        self.parent = parent
        self.node = parent.node._f_get_child(name)
        self.node_kind = 'group'

        self.has_view = False

        # Attributes that the tree of databases view will use
        # name --> DisplayRole
        # nodepath --> ToolTipRole
        # as_record --> StatusTipRole
        # icon --> DecorationRole
        self.name = name
        parentpath = parent.nodepath
        if parentpath.endswith('/'):
            parentpath = parentpath[:-1]
        self.nodepath = '{0}/{1}'.format(parentpath, name)
        self.filepath = parent.filepath
        self.as_record = '{0}->{1}'.format(self.filepath, self.nodepath)
        icons = vitables.utils.getIcons()
        self.closed_folder = icons['folder']
        self.open_folder = icons['document-open-folder']
        self.icon = icons['folder']


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
