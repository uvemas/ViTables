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
#       $Id: leafModel.py 1083 2008-11-04 16:41:02Z vmas $
#
########################################################################

"""
Here is defined the LeafModel class.

Classes:

* LeafModel(QtCore.QAbstractItemModel)

Methods:


Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tempfile
import os
import sets
import exceptions

import tables

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils

class LeafModel(QtCore.QAbstractTableModel):
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

        QtCore.QAbstractTableModel.__init__(self, parent)

        # The model data source (a PyTables/HDF5 leaf) and its access buffer
        self.data_source = rbuffer.data_source
        self.rbuffer = rbuffer

        # The number of digits of the last row
        self.last_row_width = len(str(self.rbuffer.leaf_numrows))

        #
        # The table dimensions
        #

        # The dataset number of rows is potentially huge but tables are
        # kept small: just the data returned by a read operation of the
        # buffer are displayed
        self.numrows = self.rbuffer.leafNumberOfRows()

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
        if isinstance(self.data_source, tables.VLArray):
            type = self.data_source.atom.type
            if type == 'object':
                self.formatContent = vitables.utils.formatObjectContent
            elif type in ('vlstring', 'vlunicode'):
                self.formatContent = vitables.utils.formatStringContent

        # Populate the model with the first chunk of data
        self.loadData(self.rbuffer.start, self.rbuffer.chunk_size)


    def __tr(self, source, comment=None):
        """Translate method."""
        return str(QtGui.qApp.translate('LeafModel', source, comment))


    def headerData(self, section, orientation, role):
        """Returns the data for the given role and section in the header
        with the specified orientation.
        """

        # The section alignment
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return QtCore.QVariant(\
                    int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter))
            return QtCore.QVariant(\
                int(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter))
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        # The section label for horizontal header
        if orientation == QtCore.Qt.Horizontal:
            # For tables horizontal labels are column names, for arrays
            # the section numbers are used as horizontal labels
            if hasattr(self.data_source, 'description'):
                return QtCore.QVariant(self.data_source.colnames[section])
            return QtCore.QVariant(str(section + 1))
        # The section label for vertical header
        return QtCore.QVariant(str(self.rbuffer.start + section + 1))


    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QtCore.QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), index.column())
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.formatContent(cell))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.QVariant(int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop))
        else:
            return QtCore.QVariant()


    def columnCount(self, index=QtCore.QModelIndex()):
        """The number of columns of the table.

        :Parameter index: the index of the node being inspected.
        """
        return self.numcols


    def rowCount(self, index=QtCore.QModelIndex()):
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
        self.emit(QtCore.SIGNAL("headerDataChanged(int, int, int)"), 
                    QtCore.Qt.Vertical, 0, self.numrows - 1)

