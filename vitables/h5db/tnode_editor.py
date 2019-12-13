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
This module provides editing capabilities for PyTables leaves and groups.

The module defines methods for deleting, cutting, copying, pasting and
moving nodes. Also group creation is supported.
"""

__docformat__ = 'restructuredtext'

import os

import tables

import vitables.utils



class TNodeEditor(object):
    """
    An editor for `tables.Leaf` and `tables.Group` instances.
    """

    def __init__(self, dbdoc):
        """
        Initialises the Leaf/Group editor.

        :Parameter h5file: the DBDoc instance being operated
        """

        if not dbdoc.hidden_group:
            dbdoc.createHiddenGroup()

        self.h5file = dbdoc.h5file
        self.hidden_group = dbdoc.hidden_group


    def delete(self, nodepath):
        """Delete a node.

        :Parameters:

        - `nodepath`: the full path of the node/link being deleted
        """

        try:
            self.h5file.remove_node(where=nodepath, recursive=True)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def cut(self, nodepath):
        """Moves a node to a hidden group of its database.

        The cut node must be stored somewhere or it will no be possible
        to paste it later. Storing it in the same database is extremely
        fast independently of the node size. Storing it in other database
        (i.e. in the temporary database) would have a cost which depends
        on the size of the cut node.

        :Parameters:

        - `nodepath`: the path of the node being cut
        """

        nodename = os.path.basename(nodepath)
        try:
            # The hidden group should contain at most 1 node
            for node in self.h5file.list_nodes(self.hidden_group):
                self.delete(node._v_pathname)

            self.move(nodepath, self, self.hidden_group, nodename)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def paste(self, src_node, parent, childname):
        """Copy a node to a different location.

        :Parameters:

        - `src_node`: the tables.Node instance being pasted
        - `parent`: the tables.Group where src_node will be pasted
        - `childname`: the new name of the node being pasted
        """

        try:
            self.h5file.copy_node(src_node, newparent=parent,
                newname=childname, overwrite=True, recursive=True)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def rename(self, nodepath, new_name):
        """
        Rename the selected node from the object tree.

        :Parameters:

        - `nodepath`: the full path of the node being renamed
        - `new_name`: the node new name
        """

        where, current_name = os.path.split(nodepath)

        try:
            self.h5file.rename_node(where, new_name, current_name, overwrite=1)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def create_group(self, where, final_name):
        """
        Create a new group under the given location.

        :Parameters:

        - `where`: the full path of the parent node
        - `final_name`: the new group name
        """

        try:
            if final_name in self.h5file.get_node(where)._v_children.keys():
                self.h5file.remove_node(where, final_name, recursive=True)
            self.h5file.create_group(where, final_name, title='')
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def move(self, childpath, dst_dbdoc, parentpath, childname):
        """Move a node to a different location.

        :Parameters:

        - `childpath`: the full path of the node being moved
        - `dst_dbdoc`: the destination database (a :meth:`DBDoc` instance)
        - `parentpath`: the full path of the new parent node
        - `childname`: the name of the node in its final location
        """

        try:
            dst_h5file = dst_dbdoc.h5file
            parent_node = dst_h5file.get_node(parentpath)
            if self.h5file is dst_h5file:
                self.h5file.move_node(childpath, newparent=parent_node,
                    newname=childname, overwrite=True)
            else:
                self.h5file.copy_node(childpath, newparent=parent_node,
                    newname=childname, overwrite=True, recursive=True)
                dst_h5file.flush()
                src_where, src_nodename = os.path.split(childpath)
                self.h5file.remove_node(src_where, src_nodename, recursive=1)
            self.h5file.flush()
            return childname
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()
            return None
