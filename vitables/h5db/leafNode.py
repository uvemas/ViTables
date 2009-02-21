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
Here is defined the LeafNode class.

Classes:

* LeafNode(object)

Methods:

* __init__(self, parent, name)
* row(self)

Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tables

import vitables.utils

class LeafNode(object):
    """
    A leaf node in the tree of databases model.
    """

    def __init__(self, parent, name):
        """Create a leaf node for the tree of databases model.

        A LeafNode represents a leaf of a HDF5 file and has
        a parent (a group node of the tree of databases model) and
        a name.

        :Parameters:

        - `parent`: the parent of the node.
        - `name`: the name of the node
        """

        self.parent = parent
        self.node = parent.node._f_getChild(name)

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
        self.nodepath = '%s/%s' % (parentpath, name)
        self.filepath = parent.filepath
        self.as_record = '%s->%s' % (self.filepath, self.nodepath)

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
            self.node_kind = 'unimplemented'
            self.icon = icons['unimplemented']


    def row(self):
        """The position of this node in the parent's list of children.
        """

        if self.parent:
            return self.parent.children.index(self)

        return 0

