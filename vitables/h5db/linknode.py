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
tree. The data structure is equivalent to a link node in a `PyTables` file.
"""

__docformat__ = 'restructuredtext'

import tables

import vitables.utils
from vitables.h5db import tlink_editor
from vitables.nodeprops import nodeinfo
from vitables.nodeprops import linkpropdlg

class LinkNode(object):
    """
    A leaf node in the tree of databases model.

    :Parameters:

    - `parent`: the parent of the node.
    - `name`: the name of the node
    """

    def __init__(self, model, parent, name):
        """Create a link node for the tree of databases model.

        A LinkNode represents a link (soft or external) of a `PyTables`
        file and has a parent (a group node of the tree of databases
        model) and a name.
        """

        self.dbt_model = model
        self.parent = parent
        self.node = parent.node._f_get_child(name)
        if isinstance(self.node(), tables.link.Link):
            self.node = self.node()

        self.has_view = False

        self.target = self.node.target
        if hasattr(self.target, 'extfile'):
            self.link_type = 'external'
        else:
            self.link_type = 'soft'

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
        self.as_record = '{0}'.format(self.node)

        # Set the node icon
        icons = vitables.utils.getIcons()
        if isinstance(self.node(), tables.Table):
            self.node_kind = 'table'
            self.icon = icons['link_table']
        elif isinstance(self.node(), tables.VLArray):
            self.node_kind = 'vlarray'
            data_type = self.node().atom.type
            if data_type in ['vlstring', 'vlunicode']:
                self.icon = icons['vlstring']
            elif data_type == 'object':
                self.icon = icons['object']
            else:
                self.icon = icons['link_vlarray']
        elif isinstance(self.node(), tables.EArray):
            self.node_kind = 'earray'
            self.icon = icons['link_earray']
        elif isinstance(self.node(), tables.CArray):
            self.node_kind = 'carray'
            self.icon = icons['link_carray']
        elif isinstance(self.node(), tables.Array):
            self.node_kind = 'array'
            self.icon = icons['link_array']
        elif isinstance(self.node(), tables.UnImplemented):
            self.node_kind = 'image-missing'
            self.icon = icons['image-missing']


    def row(self):
        """The position of this node in the parent's list of children.
        """

        if self.parent:
            return self.parent.children.index(self)

        return 0


    def editor(self):
        """Return an instance of `TLinkEditor`.
        """
        return tlink_editor.TLinkEditor(self.dbt_model.getDBDoc(self.filepath))


    def properties(self):
        """The Properties dialog for this node.
        """

        info = nodeinfo.NodeInfo(self)
        linkpropdlg.LinkPropDlg(info)
