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
This module defines some convenience functions for dealing with filenodes.

Efficiently managing filenodes is pretty difficult as they behave as regular
text files. By design, regular files I/O is not optimized for performing well
when the files are huge. In fact, even medium size files perform poorly. The
linecache module helps a little with this problem but at a price: it holds the
whole file in memory.
"""

import tempfile
import os

from tables.nodes import filenode

import vitables.utils as vtutils


def isFilenode(leaf):
    """Find out if PyTables node is tied to a filenode."""

    is_filenode = False
    try:
        file = leaf._v_file
        nodepath = leaf._v_pathname
        if file.get_node_attr(nodepath, 'NODE_TYPE') == filenode.NodeType:
            is_filenode = True
    except AttributeError:
        pass
    finally:
        return is_filenode


def filenodeToFile(leaf):
    """Write to disk a filenode as a regular text file."""

    # Warning: this is SLOW for large files
    fd, temp_filename = tempfile.mkstemp('.txt', 'filenode_')
    os.close(fd)
    h5file = leaf._v_file
    where = leaf._v_parent._v_pathname
    name = leaf._v_name
    filenode.read_from_filenode(h5file, temp_filename, where, name, overwrite=True)
    return vtutils.forwardPath(temp_filename)


def filenodeTotalRows(leaf):
    """Traverse the whole filenode and count its number of rows."""

    # Warning: this is SLOW for large files
    counter = 0
    with filenode.open_node(leaf, 'r') as f:
        for l in f:
            counter += 1
    return counter
