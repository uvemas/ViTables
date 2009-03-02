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
Here is defined the LeafModel class.

Classes:

* LeafModel(QAbstractItemModel)

Methods:


Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'LeafModel'

import tempfile
import os
import sets
import exceptions
import time

import tables

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils

class LeafModel(QAbstractTableModel):
    """
    The model for real data contained in leaves.

    The data is read from data sources (i.e., HDF5/PyTables nodes) by
    the model.
    """

    def __init__(self, rbuffer, parent=None):
        """Create the model.

        :Parameters:

            - `rbuffer`: a buffer used for optimizing read access to data
            - `parent`: the parent of the model
        """

        QAbstractTableModel.__init__(self, parent)

        # The model data source (a PyTables/HDF5 leaf) and its access buffer
        self.data_source = rbuffer.data_source
        self.rbuffer = rbuffer

        # The indices of columns containing time series (if any)
        self.time_cols = []

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

        # Format time series (if they are found)
        plugins = vitables.utils.registeredPlugins()
        if 'time_series' in plugins:
            import vitables.plugins.time_series as time_series
            ts_formatter = time_series.TSFormatter(self.data_source)
            self.time_cols = ts_formatter.ts_positions
            if self.time_cols != []:
                if ts_formatter.ts_kind == 'scikits_ts':
                    import scikits.timeseries as ts           
                    self.ts_frequency = ts_formatter.ts_frequency
                self.formatTime = ts_formatter.formatTime
                if self.time_cols == [-1]:
                    self.formatContent = self.formatTime

        if not isinstance(self.data_source, tables.Table):
            # Leaf is some kind of PyTables array
            atom_type = self.data_source.atom.type
            if atom_type == 'object':
                self.formatContent = vitables.utils.formatObjectContent
            elif atom_type in ('vlstring', 'vlunicode'):
                self.formatContent = vitables.utils.formatStringContent

        # Populate the model with the first chunk of data
        self.loadData(self.rbuffer.start, self.rbuffer.chunk_size)

    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.
        """

        # The section alignment
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return QVariant(\
                    int(Qt.AlignLeft|Qt.AlignVCenter))
            return QVariant(\
                int(Qt.AlignRight|Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return QVariant()
        # The section label for horizontal header
        if orientation == Qt.Horizontal:
            # For tables horizontal labels are column names, for arrays
            # the section numbers are used as horizontal labels
            if hasattr(self.data_source, 'description'):
                return QVariant(self.data_source.colnames[section])
            return QVariant(unicode(section + 1))
        # The section label for vertical header
        return QVariant(unicode(self.rbuffer.start + section + 1))

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), index.column())
        if role == Qt.DisplayRole:
            if index.column() in self.time_cols:
                return QVariant(self.formatTime(cell))
            return QVariant(self.formatContent(cell))
        elif role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignLeft|Qt.AlignTop))
        else:
            return QVariant()

    def columnCount(self, index=QModelIndex()):
        """The number of columns of the table.

        :Parameter index: the index of the node being inspected.
        """
        return self.numcols

    def rowCount(self, index=QModelIndex()):
        """The number of rows of the table.

        :Parameter index: the index of the node being inspected.
        """
        return self.numrows

    def loadData(self, start, chunk_size):
        """Load the model with fresh data from the buffer.

        :Parameters:

            - `start`: the row where the buffer starts
            - `chunk_size`: the size of the buffer
        """

        self.rbuffer.readBuffer(start, chunk_size)
        self.emit(SIGNAL("headerDataChanged(int, int, int)"), 
                    Qt.Vertical, 0, self.numrows - 1)

