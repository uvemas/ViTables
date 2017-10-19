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
This module implements a model (in the `MVC` sense) for the real data stored
in a `tables.Leaf`.
"""

import logging

import tables

from qtpy import QtCore

import vitables.utils
from vitables.vttables import buffer
from vitables.vttables import filenodebuffer

__docformat__ = 'restructuredtext'

#: The maximum number of rows to be read from the data source.
CHUNK_SIZE = 10000

log = logging.getLogger(__name__)


class LeafModel(QtCore.QAbstractTableModel):
    """
    The model for real data contained in leaves.

    The data is read from data sources (i.e., `HDF5/PyTables` nodes) by
    the model.
    The dataset number of rows is potentially huge but tables are read and
    displayed in chunks.


    :param parent:
        The parent of the model, passed as is in the superclass.
    :attribute leaf:
        the underlying hdf5 data
    :attribute rbuffer:
        Code for chunking and inspecting the undelying data.
    :attribute leaf_numrows:
        the total number of rows in the underlying data
    :attribute numrows:
        The number of rows visible which equals the chunking-size.
    :attribute numcols:
        The total number of columnss visible, equal to those visible.
    :attribute start:
        The zero-based starting index of the chunk within the total rows.

    """

    def __init__(self, leaf, parent=None):
        """Create the model.
        """

        # The model data source (a PyTables/HDF5 leaf) and its access buffer
        self.leaf = leaf
        self.is_filenode = False
        vtapp = vitables.utils.getApp()
        if leaf in vtapp.filenodes_map:
            self.is_filenode = True
            self.rbuffer = filenodebuffer.FilenodeBuffer(leaf)
        else:
            self.rbuffer = buffer.Buffer(leaf)

        self.leaf_numrows = self.rbuffer.total_nrows()
        self.numrows = min(self.leaf_numrows, CHUNK_SIZE)
        self.start = 0

        # The dataset number of columns doesn't use to be large so, we don't
        # need set a maximum as we did with rows. The whole set of columns
        # are displayed
        if isinstance(leaf, tables.Table):
            # Leaf is a PyTables table
            self.numcols = len(leaf.colnames)
        elif isinstance(leaf, tables.EArray):
            self.numcols = 1
        else:
            # Leaf is some kind of PyTables array
            shape = leaf.shape
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

        if self.is_filenode:
            self.formatContent = vitables.utils.formatStringContent
        elif not isinstance(leaf, tables.Table):
            # Leaf is some kind of PyTables array
            atom_type = leaf.atom.type
            if atom_type == 'object':
                self.formatContent = vitables.utils.formatObjectContent
            elif atom_type in ('vlstring', 'vlunicode'):
                self.formatContent = vitables.utils.formatStringContent
            else:
                self.formatContent = vitables.utils.formatArrayContent
        else:
            self.formatContent = vitables.utils.formatArrayContent

        # Track selected cell
        self.selected_cell = {'index': QtCore.QModelIndex(), 'buffer_start': 0}

        # Populate the model with the first chunk of data
        self.loadData(0, self.numrows)

        super(LeafModel, self).__init__(parent)

    def columnCount(self, index=QtCore.QModelIndex()):
        """The number of columns of the given model index.

        Overridden to return 0 for valid indices because they have no children;
        otherwise return the total number of *columns* exposed by the model.

        :param index:
            the model index being inspected.
        """

        return 0 if index.isValid() else self.numcols

    def rowCount(self, index=QtCore.QModelIndex()):
        """The number of columns for the children of the given index.

        Overridden to return 0 for valid indices because they have no children;
        otherwise return the total number of *rows* exposed by the model.

        :Parameter index: the model index being inspected.
        """

        return 0 if index.isValid() else self.numrows

    def loadData(self, start, length):
        """Load the model with fresh data from the buffer.

        :param start:
            the document row that is the first row of the chunk.
        :param length:
            the buffer size, i.e. the number of rows to be read.

        :return:
            a tuple with tested values for the parameters of the read method
        """

        # Enforce scrolling limits.
        #
        start = max(start, 0)
        stop = min(start + length, self.leaf_numrows)

        # Ensure buffer filled when scrolled beyond bottom.
        #
        actual_start = stop - self.numrows
        start = max(min(actual_start, start), 0)

        self.rbuffer.readBuffer(start, stop)
        self.start = start

    def get_corner_span(self):
        """Must return ``(row_span, col_span)`` tuple for the top-left cell."""
        return 1, 1

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
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

        if role != QtCore.Qt.DisplayRole:
            return None

        # Columns-labels
        if orientation == QtCore.Qt.Horizontal:
            # For tables horizontal labels are column names, for arrays
            # the section numbers are used as horizontal labels
            if hasattr(self.leaf, 'description'):
                return str(self.leaf.colnames[section])
            return str(section)

        # Rows-labels
        return str(self.start + section)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        row, col = index.row(), index.column()

        if not index.isValid() or not (0 <= row < self.numrows):
            return None

        if role == QtCore.Qt.DisplayRole:
            cell = self.cell(row, col)
            return self.formatContent(cell)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

        return None

    def cell(self, row, col):
        """
        Returns the contents of a cell.

        :return: none to disable zooming.
        """
        try:
            return self.rbuffer.getCell(row, col)
        except IndexError:
            log.error('IndexError! buffer start: {0} row, column: '
                      '{1}, {2}'.format(self.start, row, col))
