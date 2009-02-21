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
Here is defined the NodeInfo class.

Classes:

* NodeInfo

Methods:


Functions:


Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import os.path



class NodeInfo(object):
    """Collects information about a given node.

    The following data and metadata can be collected:
    * format of the database (generic HDF5 or PyTables)
    * filename of the database
    * filepath of the database
    * opening mode of the database
    * size of the database
    * node type
    * node name
    * node path
    * for Group nodes:
        - attributes set instance and related info
        - dictionary of nodes hanging from a group
        - dictionary of groups hanging from a group
        - dictionary of leaves hanging from a group
    * for Table nodes:
        - columns names, datatypes and shapes
        - number of rows and columns
        - filters
        - shape
        - flavor
    * for XArray nodes:
        - number of rows
        - datatype
        - filters
        - shape
        - flavor
    """

    def __init__(self, node_item):
        """Collects information about a given node.

        Some PyTables string attributes are regular Python strings instead
        of unicode strings and have to be explicitely converted to unicode.

        node_item is an instance of RootGroupNode, GroupNode or LeafNode.
        """

        self.node = node_item.node

        # The hosting File instance, filepath, filename and opening mode
        self.h5file = self.node._v_file
        self.filepath = self.h5file.filename
        self.filename = os.path.basename(self.filepath)
        mode = self.h5file.mode
        if mode == 'a':
            self.mode = unicode('append', 'utf_8')
        elif mode == 'r':
            self.mode = unicode('read-only', 'utf_8')
        else:
            self.mode = unicode('read-write', 'utf_8')

        # The node type is a string with one of the following values:
        # root group, group, table, vlarray, earray, carray, array
        # or unimplemented
        self.node_type = node_item.node_kind
        self.file_type = self.format + ', ' + self.size
        self.nodename = self.node._v_name
        self.nodepath = self.node._v_pathname

        # The attributes set instance
        self.asi = self.node._v_attrs
        sysattrs_names = self.asi._v_attrnamessys
        self.system_attrs = \
            dict((n, getattr(self.asi, n, None)) for n in sysattrs_names)
        userattrs_names = self.asi._v_attrnamesuser
        self.user_attrs = \
            dict((n, getattr(self.asi, n, None)) for n in userattrs_names)


    # Properties for File instances

    def _format(self):
        """The format of the hosting File instance"""
        if self.h5file._isPTFile:
            return unicode('PyTables file', 'utf_8')
        else:
            return unicode('Generic HDF5 file', 'utf_8')

    format = property(fget=_format)


    def _size(self):
        """The size of the hosting File instance"""

        bytes = os.path.getsize(self.filepath) *1.0
        kbytes = bytes/1024
        mbytes = kbytes/1024
        gbytes = mbytes/1024
        tbytes = gbytes/1024
        if kbytes < 1:
            size = '%d bytes' % bytes
        elif mbytes < 1:
            size = '%.0f KB' % (kbytes)
        elif gbytes < 1:
            size = '%.0f MB' % (mbytes)
        elif tbytes < 1:
            size = '%.0f GB' % (gbytes)
        else:
            size = '%.0f TB' % (tbytes)
        return unicode(size, 'utf_8')

    size = property(fget=_size)


    # Properties for Group instances

    def _hangingNodes(self):
        """The dictionary of nodes hanging from this group."""

        try:
            return self.node._v_children
        except AttributeError:
            return {}

    hanging_nodes = property(fget=_hangingNodes)


    def _hangingGroups(self):
        """The dictionary of groups hanging from this group."""

        try:
            return self.node._v_groups
        except AttributeError:
            return {}

    hanging_groups = property(fget=_hangingGroups)


    def _hangingLeaves(self):
        """The dictionary of leaves hanging from this group."""

        try:
            return self.node._v_leaves
        except AttributeError:
            return {}

    hanging_leaves = property(fget=_hangingLeaves)


    # Properties for Leaf instances

    def _dtype(self):
        """The numpy dtype that most closely matches the atom of this leaf."""

        if self.node_type.count('array'):
            try:
                return unicode(self.node.atom.type, 'utf_8')
            except AttributeError:
                return None
        elif self.node_type == 'table':
            return unicode('record', 'utf_8')

    dtype = property(fget=_dtype)


    def _nrows(self):
        """The current number of rows in the table/array node."""

        try:
            return self.node.shape[0]
        except TypeError:  #  shape is None
            return 0
        except IndexError:  # numpy scalar arrays have shape = ()
            return 1

    nrows = property(fget=_nrows)


    def _shape(self):
        """The shape of data in the table/array node."""

        try:
            return self.node.shape
        except AttributeError:
            return None

    shape = property(fget=_shape)


    def _flavor(self):
        """The type of data object read from the table/array node."""

        try:
            return unicode(self.node.flavor, 'utf_8')
        except AttributeError:
            return None

    flavor = property(fget=_flavor)


    def _filters(self):
        """Filters property for this table/array node."""

        try:
            return self.node.filters
        except AttributeError:
            return None

    filters = property(fget=_filters)


    # Properties for Table instances

    def _colNames(self):
        """A list containing the names of top-level columns in the table."""

        try:
            return self.node.colnames
        except AttributeError:
            return []

    columns_names = property(fget=_colNames)


    def _colPathNames(self):
        """A list containing the paths of top-level columns in the table."""

        try:
            return self.node.colpathnames
        except AttributeError:
            return []

    columns_pathnames = property(fget=_colPathNames)


    def _colTypes(self):
        """A mapping between the name of the table columns and their datatypes.
        """

        try:
            return self.node.coltypes
        except AttributeError:
            return {}

    columns_types = property(fget=_colTypes)


    def _colShapes(self):
        """A mapping between the shape of the table columns and their names.
        """

        try:
            coldescrs = self.node.coldescrs
            return dict((k, v.shape) for (k, v) in coldescrs.iteritems())
        except AttributeError:
            return {}

    columns_shapes = property(fget=_colShapes)


    def _ncolumns(self):
        """The current number of columns in the table node."""

        try:
            return len(self.node.columns_names)
        except AttributeError:
            return None

    ncolumns = property(fget=_ncolumns)


