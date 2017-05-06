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
This module provides editing capabilities for PyTables soft and external links.

The module defines methods for deleting, cutting, copying, pasting and
moving links.
"""

__docformat__ = 'restructuredtext'

import os

import tables

import vitables.utils



class TLinkEditor(object):
    """
    An editor for `tables.Link` instances.
    """

    def __init__(self, dbdoc):
        """
        Initialises the tables.Link editor.

        :Parameter h5file: the tables.File instance being operated
        """

        if not dbdoc.hidden_group:
            dbdoc.createHiddenGroup()

        self.h5file = dbdoc.h5file
        self.hidden_group = dbdoc.hidden_group


    def delete(self, nodepath):
        """Delete a link.

        :Parameters:

        - `nodepath`: the full path of the node/link being deleted
        """

        try:
            link = self.h5file.get_node(nodepath)
            link.remove()
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def cut(self, nodepath):
        """Moves a link to a hidden group of its database.

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
                self.h5file.deleteNode(node._v_pathname)

            link = self.h5file.get_node(nodepath)
            link.move(newparent=self.hidden_group, newname=nodename)
            self.h5file.flush()
        except(tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def paste(self, link, parent, childname):
        """Copy a link to a different location.

        :Parameters:

        - `link`: the tables.link instance being pasted
        - `parent`: the new parent of the node being pasted
        - `childname`: the new name of the node being pasted
        """

        try:
            link.copy(newparent=parent, newname=childname,
                overwrite=True, createparents=False)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def rename(self, nodepath, new_name):
        """
        Rename the selected link from the object tree.

        :Parameters:

        - `nodepath`: the full path of the node being renamed
        - `new_name`: the node new name
        """

        try:
            link = self.h5file.get_node(nodepath)
            link.rename(new_name)
            self.h5file.flush()
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()


    def move(self, childpath, dst_dbdoc, parentpath, childname):
        """Move a ink to a different location.

        :Parameters:

        - `childpath`: the full path of the node being moved
        - `dst_dbdoc`: the destination database (a :meth:`DBDoc` instance)
        - `parentpath`: the full path of the new parent node
        - `childname`: the name of the node in its final location
        """

        try:
            dst_h5file = dst_dbdoc.h5file
            parent_node = dst_h5file.get_node(parentpath)
            link = self.h5file.get_node(childpath)
            if self.h5file is dst_h5file:
                link.move(newparent=parentpath, newname=childname)
            else:
                link.copy(newparent=parent_node, newname=childname)
                dst_h5file.flush()
                src_where, src_nodename = os.path.split(childpath)
                self.h5file.remove_node(src_where, src_nodename, recursive=1)
            self.h5file.flush()
            return childname
        except (tables.NodeError, OSError):
            vitables.utils.formatExceptionInfo()
            return None
