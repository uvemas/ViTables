#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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
This module implements a model (in the `MVC` sense) for the real data stored 
in a `tables.Leaf`.
"""

__docformat__ = 'restructuredtext'

import tables

from PyQt4 import QtCore

import vitables.utils

class LeafModel(QtCore.QAbstractTableModel):
    """
    The model for real data contained in leaves.

    The data is read from data sources (i.e., `HDF5/PyTables` nodes) by
    the model.

    :Parameters:

        - `rbuffer`: a buffer used for optimizing read access to data
        - `parent`: the parent of the model
    """

    def __init__(self, rbuffer, parent=None):
        """Create the model.
        """

        # The model data source (a PyTables/HDF5 leaf) and its access buffer
        self.data_source = rbuffer.data_source
        self.rbuffer = rbuffer

        # The number of digits of the last row
        self.last_row_width = len(unicode(self.rbuffer.leaf_numrows))

        #
        # The table dimensions
        #

        # The dataset number of rows is potentially huge but tables are
        # kept small: just the data returned by a read operation of the
        # buffer are displayed
        self.numrows = self.rbuffer.leafNumberOfRows()
        if self.numrows > self.rbuffer.chunk_size:
            self.numrows = self.rbuffer.chunk_size

        # The dataset number of columns doesn't use to be large so, we don't
        # need set a maximum as we did with rows. The whole set of columns
        # are displayed
        if isinstance(self.data_source, tables.Table):
            # Leaf is a PyTables table
            self.numcols = len(self.data_source.colnames)
        elif isinstance(self.data_source, tables.EArray):
            self.numcols = 1
        else:
            # Leaf is some kind of PyTables array
            shape = self.data_source.shape
            if len(shape) > 1:
                # The leaf will be displayed as a bidimensional matrix
                self.numcols = shape[1]
            else:
                # The leaf will be displayed as a column vector
                self.numcols = 1

        #
        # Choose a format for cells
        #

        self.formatContent = vitables.utils.formatArrayContent

        # Time series (if they are found) are formatted transparently
        # via the time_series.py plugin

        if not isinstance(self.data_source, tables.Table):
            # Leaf is some kind of PyTables array
            atom_type = self.data_source.atom.type
            if atom_type == 'object':
                self.formatContent = vitables.utils.formatObjectContent
            elif atom_type in ('vlstring', 'vlunicode'):
                self.formatContent = vitables.utils.formatStringContent

        # Track selected cell
        self.selected_cell = {'index': QtCore.QModelIndex(), 'buffer_start': 0}

        # Populate the model with the first chunk of data
        self.loadData(self.rbuffer.start, self.rbuffer.chunk_size)

        super(LeafModel, self).__init__(parent)


    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.

        This is an overwritten method.

        :Parameters:

        - `section`: the header section being inspected
        - `orientation`: the header orientation (horizontal or vertical)
        - `role`: the role of the header section being inspected
        """

        # The section alignment
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            return int(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        if role != QtCore.Qt.DisplayRole:
            return None
        # The section label for horizontal header
        if orientation == QtCore.Qt.Horizontal:
            # For tables horizontal labels are column names, for arrays
            # the section numbers are used as horizontal labels
            if hasattr(self.data_source, 'description'):
                return unicode(self.data_source.colnames[section])
            return unicode(section + 1)
        # The section label for vertical header. This is a 64 bits integer
        return unicode(self.rbuffer.start + section + 1)


    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return None
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), 
            index.column())
        if role == QtCore.Qt.DisplayRole:
            return self.formatContent(cell)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        else:
            return None


    def columnCount(self, index=QtCore.QModelIndex()):
        """The number of columns of the given model index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of columns exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numcols
        else:
            return 0


    def rowCount(self, index=QtCore.QModelIndex()):
        """The number of columns for the children of the given index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of rows exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numrows
        else:
            return 0


    def loadData(self, start, chunk_size):
        """Load the model with fresh data from the buffer.

        :Parameters:

        - `start`: the row where the buffer starts
        - `chunk_size`: the size of the buffer
        """
        self.rbuffer.readBuffer(start, chunk_size)
