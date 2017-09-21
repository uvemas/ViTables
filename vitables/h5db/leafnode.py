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
tree. The data structure is equivalent to a leaf node in a `PyTables` file.
"""

import tables
from tables.nodes import filenode

import vitables.utils
from vitables.h5db import tnode_editor
from vitables.nodeprops import nodeinfo
from vitables.nodeprops import leafpropdlg


__docformat__ = 'restructuredtext'


class LeafNode(object):
    """
    A leaf node in the tree of databases model.

    :Parameters:

    - `parent`: the parent of the node.
    - `name`: the name of the node
    """

    def __init__(self, model, parent, name):
        """Create a leaf node for the tree of databases model.

        A LeafNode represents a leaf of a `HDF5` file and has
        a parent (a group node of the tree of databases model) and
        a name.
        """

        self.dbt_model = model
        self.parent = parent
        self.node = parent.node._f_get_child(name)

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

        # Set the node icon
        icons = vitables.utils.getIcons()
        if isinstance(self.node, tables.Table):
            self.node_kind = 'table'
            self.icon = icons['table']
        elif isinstance(self.node, tables.VLArray):
            self.node_kind = 'vlarray'
            data_type = self.node.atom.type
            if data_type in ['vlstring', 'vlunicode']:
                self.icon = icons['vlstring']
            elif data_type == 'object':
                self.icon = icons['object']
            else:
                self.icon = icons['vlarray']
        elif isinstance(self.node, tables.EArray):
            self.node_kind = 'earray'
            self.icon = icons['earray']
        elif isinstance(self.node, tables.CArray):
            self.node_kind = 'carray'
            self.icon = icons['carray']
        elif isinstance(self.node, tables.Array):
            self.node_kind = 'array'
            self.icon = icons['array']
        elif isinstance(self.node, tables.UnImplemented):
            self.node_kind = 'image-missing'
            self.icon = icons['image-missing']
        try:
            file = self.node._v_file
            if file.get_node_attr(self.nodepath, 'NODE_TYPE') == filenode.NodeType:
                self.node_kind = 'earray (filenode)'
                self.icon = icons['filenode']
        except AttributeError:
            pass

    def row(self):
        """The position of this node in the parent's list of children.
        """

        if self.parent:
            return self.parent.children.index(self)

        return 0

    def editor(self):
        """Return an instance of `TNodeEditor`.
        """
        return tnode_editor.TNodeEditor(self.dbt_model.getDBDoc(self.filepath))

    def properties(self):
        """The Properties dialog for this node.
        """

        info = nodeinfo.NodeInfo(self)
        leafpropdlg.LeafPropDlg(info)
