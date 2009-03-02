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
Here is defined the RootGroupNode class.

Classes:

* RootGroupNode(object)

Methods:

* __init__(self, data_source=None, parent=None, tmp_db=False)
* __len__(self)
* findChild(self, childname)
* insertChild(self, child)
* childAtRow(self, row)
* rowOfChild(self, child)
* row(self)

Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import vitables.utils

class RootGroupNode(object):
    """
    A root group node in the tree of databases model.

    Root group nodes are top level nodes (i.e., they have no parent).
    """

    def __init__(self, data_source=None, parent=None, tmp_db=False):
        """Create the root group node for the tree of databases model.

        The root of the tree of databases model is a RootGroupNode with
        no parent and no data source. Any other RootGroupNode represents
        a root group of a HDF5 file and has a parent (the root of the
        tree of databases model) and a data source (the HDF5 file).

        :Parameters:

        - `data_source`: the data source of the node.
        - `parent`: the parent of the node.
        - `tmp_db`: True if the node is tied to the temporary database
        """

        self.children = []
        self.parent = parent
        self.name = u'root node'
        self.filepath = None
        if data_source:
            self.node = data_source.getNode(u'/')
            self.node_kind = u'root group'

            self.has_view = False

            # Attributes that the tree of databases view will use
            # name --> DisplayRole
            # nodepath --> ToolTipRole
            # as_record --> StatusTipRole
            # icon --> DecorationRole
            if tmp_db:
                self.name = u'Query results'
            else:
                self.name = data_source.filename
            self.nodepath = u'/'
            self.filepath = data_source.filepath
            self.as_record = u'%s->%s' % (self.filepath, self.nodepath)
            self.mode = data_source.mode
            icons = vitables.utils.getIcons()
            if tmp_db:
                self.icon = icons[u'dbfilters']
            elif self.mode == u'r':
                self.icon = icons[u'file_ro']
            else:
                self.icon = icons[u'file_rw']


    def __len__(self):
        return len(self.children)


    def insertChild(self, child, position=0):
        """Insert a child in a group node.

        :Parameter child: the child being inserted.
        """
        self.children.insert(position, child)


    def childAtRow(self, row):
        """Insert a child in a group node.

        :Parameter child: the child being inserted.
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
                break
        return None

