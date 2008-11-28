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
#       $Id: groupNode.py 1072 2008-10-19 09:51:20Z vmas $
#
########################################################################

"""
Here is defined the GroupNode class.

Classes:

* GroupNode(object)

Methods:

* __init__(self, parent, name)
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

class GroupNode(object):
    """
    A group node in the tree of databases model.
    """

    def __init__(self, parent, name):
        """Create a group node for the tree of databases model.

        A GroupNode represents a (non root) group of a HDF5 file and has
        a parent (another group node of the tree of databases model) and
        a name.

        :Parameters:

        - `parent`: the parent of the node.
        - `name`: the name of the node
        """

        self.children = []
        self.parent = parent
        self.node = parent.node._f_getChild(name)
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
        self.nodepath = '%s/%s' % (parentpath, name)
        self.filepath = parent.filepath
        self.as_record = '%s->%s' % (self.filepath, self.nodepath)
        icons = vitables.utils.getIcons()
        self.closed_folder = icons['folder']
        self.open_folder = icons['folder_open']
        self.icon = icons['folder']


    def __len__(self):
        return len(self.children)


    def insertChild(self, child):
        """Insert a child in a group node.

        :Parameter child: the child being inserted.
        """

        self.children = [child] + self.children


    def childAtRow(self, row):
        """The row-th child of this node.

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
                break
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

