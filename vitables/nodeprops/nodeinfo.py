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
This module collects information about a given node of a `PyTables` database.
"""

__docformat__ = 'restructuredtext'

import os.path

import vitables.utils

class NodeInfo(object):
    """Collects information about a given node.

    The following data and metadata can be collected:

    * format of the database (generic `HDF5` or `PyTables`)
    * filename of the database
    * filepath of the database
    * opening mode of the database
    * size of the database
    * node type
    * node name
    * node path
    * for `tables.Group` nodes:

        - attributes set instance and related info
        - dictionary of nodes hanging from a group
        - dictionary of groups hanging from a group
        - dictionary of leaves hanging from a group

    * for `tables.Table` nodes:

        - columns names, datatypes and shapes
        - number of rows and columns
        - filters
        - shape
        - flavor

    * for `tables.XArray` nodes:

        - number of rows
        - datatype
        - filters
        - shape
        - flavor

    :Parameter node_item: an instance of :meth:`RootGroupNode`,
      :meth:`GroupNode` or :meth:`LeafNode`.
    """

    def __init__(self, node_item):
        """Collects information about a given node.

        Some PyTables2.X string attributes are regular Python strings instead
        of unicode strings and have to be explicitely converted to unicode.
        """

        self.node = node_item.node

        # The hosting File instance, filepath, filename and opening mode
        self.filepath = str(node_item.filepath)
        self.filename = os.path.basename(self.filepath)
        self.h5file = self.node._v_file
        mode = str(self.h5file.mode)
        if mode == 'a':
            self.mode = 'append'
        elif mode == 'r':
            self.mode = 'read-only'
        else:
            self.mode = 'read-write'

        # The node type is a string with one of the following values:
        # root group, group, table, vlarray, earray, carray, array
        # or unimplemented
        self.node_type = node_item.node_kind
        self.file_type = self.format + ', ' + self.size
        self.nodename = str(node_item.name)
        self.nodepath = str(node_item.nodepath)

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
        """The format of the hosting `tables.File` instance"""

        if self.h5file._isPTFile:
            return 'PyTables file'
        else:
            return 'Generic HDF5 file'

    format = property(fget=_format)


    def _size(self):
        """The size of the hosting `tables.File` instance"""

        n_bytes = os.path.getsize(self.filepath) *1.0
        kbytes = n_bytes/1024
        mbytes = kbytes/1024
        gbytes = mbytes/1024
        tbytes = gbytes/1024
        if kbytes < 1:
            size = '{0:.0f} bytes'.format(n_bytes)
        elif mbytes < 1:
            size = '{0:.1f} KB'.format(kbytes)
        elif gbytes < 1:
            size = '{0:.1f} MB'.format(mbytes)
        elif tbytes < 1:
            size = '{0:.1f} GB'.format(gbytes)
        else:
            size = '{0:.1f} TB'.format(tbytes)
        return size

    size = property(fget=_size)

    # Properties for Group instances

    def _hangingNodes(self):
        """The dictionary of nodes hanging from this node."""

        try:
            return self.node._v_children
        except AttributeError:
            return {}

    hanging_nodes = property(fget=_hangingNodes)


    def _hangingGroups(self):
        """The dictionary of groups hanging from this node."""

        try:
            return self.node._v_groups
        except AttributeError:
            return {}

    hanging_groups = property(fget=_hangingGroups)


    def _hangingLeaves(self):
        """The dictionary of leaves hanging from this node."""

        try:
            return self.node._v_leaves
        except AttributeError:
            return {}

    hanging_leaves = property(fget=_hangingLeaves)


    def _hangingLinks(self):
        """The dictionary of links hanging from this node."""

        try:
            return self.node._v_links
        except AttributeError:
            return {}

    hanging_links = property(fget=_hangingLinks)


    # Properties for Leaf instances

    def _type(self):
        """The `PyTables` data type of the atom for `tables.Leaf` nodes."""

        if self.node_type.count('array'):
            try:
                return str(self.node.atom.type)
            except AttributeError:
                return None
        elif self.node_type == 'table':
            return 'record'

    type = property(fget=_type)


    def _nrows(self):
        """The current number of rows in the `tables.Leaf` node."""

        try:
            return self.node.shape[0]
        except TypeError:  #  shape is None
            return 0
        except IndexError:  # numpy scalar arrays have shape = ()
            return 1

    nrows = property(fget=_nrows)


    def _shape(self):
        """The shape of data in the `tables.Leaf` node."""

        try:
            return self.node.shape
        except AttributeError:
            return None

    shape = property(fget=_shape)


    def _flavor(self):
        """The type of data object read from the `tables.Leaf` node."""

        try:
            return str(self.node.flavor)
        except AttributeError:
            return None

    flavor = property(fget=_flavor)


    def _filters(self):
        """Filters property for this `tables.Leaf` node."""

        try:
            return self.node.filters
        except AttributeError:
            return None

    filters = property(fget=_filters)

    # Properties for Table instances

    def _colNames(self):
        """The list of names of top-level columns in a `tables.Table` node."""

        try:
            return self.node.colnames
        except AttributeError:
            return []

    columns_names = property(fget=_colNames)


    def _colPathNames(self):
        """The list of paths of top-level columns in a `tables.Table` node."""

        try:
            return self.node.colpathnames
        except AttributeError:
            return []

    columns_pathnames = property(fget=_colPathNames)


    def _colTypes(self):
        """
        Mapping with `tables.Table` field names and their `PyTables` datatypes.
        """

        try:
            return self.node.coltypes
        except AttributeError:
            return {}

    columns_types = property(fget=_colTypes)


    def _colShapes(self):
        """
        Mapping with the `tables.Table` field names and their shapes.
        """

        try:
            coldescrs = self.node.coldescrs
            return dict((k, v.shape) for (k, v) in coldescrs.items())
        except AttributeError:
            return {}

    columns_shapes = property(fget=_colShapes)


    def _ncolumns(self):
        """The current number of columns in the `tables.Table` node."""

        try:
            return len(self.node.columns_names)
        except AttributeError:
            return None

    ncolumns = property(fget=_ncolumns)


    def _target(self):
        """The target of a `tables.Link` node."""

        try:
            return str(self.node.target)
        except AttributeError:
            return None

    target = property(fget=_target)


    def _link_type(self):
        """The kind of link (i.e. soft or external) of a `tables.Link` node."""

        if self.target:
            try:
                link_type = 'external'
                self.node.extfile
            except AttributeError:
                link_type = 'soft'
            return link_type
        else:
            return None

    link_type = property(fget=_link_type)


