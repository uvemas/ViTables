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

__docformat__ = 'restructuredtext'

import logging

from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt

from . import leaf_model


log = logging.getLogger(__name__)

_axis_font = QtGui.QFont()
_axis_font.setBold(True)

_axis_label_font = QtGui.QFont()
_axis_label_font.setBold(True)
_axis_label_font.setItalic(True)


def try_opening_as_dataframe(leaf):
    try:
        from pandas.io import pytables
    except ImportError:
        return

    class HDFStoreWrapper(pytables.HDFStore):
        """Subclassed to construct stores from :class:`h5py.File` instances."""

        def __init__(self, tables_h5file):
            self._path = tables_h5file.filename
            self._mode = tables_h5file.mode
            self._handle = tables_h5file
            self._filters = tables_h5file.filters

            pytables._tables()

    pgroup = leaf._g_getparent()
    assert pgroup._c_classid == 'GROUP', (leaf, pgroup)

    pandas_attr = getattr(pgroup._v_attrs, 'pandas_type', None)
    if pandas_attr in ['frame', 'frame_table']:
        hstore = HDFStoreWrapper(leaf._v_file)

        return DataFrameModel(leaf, hstore)


def get_index_name(index, i, fallback_pattern):
    """returns the name of a dataframe index."""
    val = i
    try:
        val = index.names[i]
    except:  # @IgnorePep8
        pass

    if val is None:
        val = fallback_pattern % i
    elif isinstance(val, int):
        val = fallback_pattern % val

    return val


class DataFrameModel(QtCore.QAbstractTableModel):
    """
    The model for data contained in pandas DataFrame chunks.

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
        The total number of columns visible, equal to those visible.
    :attribute start:
        The zero-based starting index of the chunk within the total rows.
    :attribute _nheaders:
        A tuple ``(row_span, col_span)`` for the number of *columns/indices*
        headers respectively, in case they are pandas multi-index, or
        just ``(1, 1)``.
    """

    def __init__(self, leaf, hstore, parent=None):
        """Create the model.
        """
        self._leaf = leaf
        self._pgroup = self._leaf._g_getparent()._v_pathname

        self._hstore = hstore
        self.start = 0

        ## The dataset number of rows is potentially huge but tables are
        #  kept small: just the data returned by a read operation of the
        #  buffer are displayed
        self.leaf_numrows = leaf.shape[0]
        self.numrows = min(self.leaf_numrows, leaf_model.CHUNK_SIZE)

        # Track selected cell.
        self.selected_cell = {'index': QtCore.QModelIndex(), 'buffer_start': 0}

        # Populate the model with the first chunk of data.
        self.loadData(0, self.numrows)
        chunk = self._chunk
        self.numcols = len(chunk.columns)

        def count_multiindex(index):
            try:
                return index.nlevels
            except AttributeError:
                return 1

        self._nheaders = tuple(count_multiindex(idx)
                               for idx
                               in (chunk.columns, chunk.index))

        super(DataFrameModel, self).__init__(parent)

    def columnCount(self, index=QtCore.QModelIndex()):
        """
        The total number of columns, or number of children for the given index.

        :param index:
            Overrides should return 0 for valid indices if no children exist)
            or the number of the total *columns* exposed by the model.
        """
        return 0 if index.isValid() else self.numcols

    def rowCount(self, index=QtCore.QModelIndex()):
        """
        The total number of rows, or number of children for the given index.

        :param index:
            Overrides should return 0 for valid indices if no children exist)
            or the number of the total *columns* exposed by the model.
        """

        return 0 if index.isValid() else self.numrows

    def loadData(self, start, length):
        """Load the model with fresh chunk from the underlying leaf.

        :param start:
            The first row (within the total nrows) of the chunk to read.
        :param length:
            The buffer size, i.e. the number of rows to be read.
        """
        ## Enforce scroll limits.
        #
        start = max(start, 0)
        stop = min(start + length, self.leaf_numrows)
        assert stop >= start, (self.numrows, start, stop, length)

        ## Ensure that the whole buffer will be filled.
        #
        actual_start = stop - self.numrows
        start = max(min(actual_start, start), 0)

        self._chunk = self._hstore.select(self._pgroup,
                                          start=start, stop=stop)
        self.start = start

    def get_corner_span(self):
        """Must return ``(row_span, col_span)`` tuple for the top-left cell."""
        return self._nheaders if self.start == 0 else (1, 1)

    def headerData(self, section, orientation, role):
        """
        Model method to return header content and formatting.

        :param section:
            The zero-based row/column number to return.
        :param orientation:
            The header orientation (horizontal := columns, vertical := index).
        :param role:
            The Qt.XXXRole: being inspected.
        """
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return Qt.AlignCenter | Qt.AlignBottom
            return Qt.AlignRight | Qt.AlignVCenter

        n_columns, n_index = self._nheaders
        is_header = ((orientation == Qt.Horizontal and
                      section < n_index) or
                     (orientation == Qt.Vertical and
                      (self.start + section) < n_columns))

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if is_header:
                    return get_index_name(self._chunk.index, section, 'I%s')
                return str(section)

            if orientation == Qt.Vertical:
                if is_header:
                    return get_index_name(self._chunk.columns, section, 'C%s')
                return str(self.start + section)

        if role == Qt.FontRole and is_header:
                return _axis_label_font

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        row, col = index.row(), index.column()
        n_columns, n_index = self._nheaders
        df = self._chunk

        if not index.isValid() or not (0 <= row < (self.numrows + n_columns)):
            return None

        is_index = col < n_index
        is_columns = (self.start + row) < n_columns

        if is_index and is_columns:
            return None

        if is_index:
            if role == Qt.DisplayRole:
                val = df.index[row]
                if n_index > 1:
                    val = val[col]
                return str(val)
            if role == Qt.FontRole:
                return _axis_font
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return

        if is_columns:
            if role == Qt.DisplayRole:
                val = df.columns[col]
                if n_columns > 1:
                    val = val[row]
                return str(val)
            if role == Qt.FontRole:
                return _axis_font
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter | Qt.AlignBottom)
            return

        if role == Qt.DisplayRole:
            return str(self._chunk.iat[row - n_columns, col - n_index])

        # if role == Qt.TextAlignmentRole:
        #     return int(Qt.AlignLeft|Qt.AlignTop)

        return

    def cell(self, row, col):
        return None  # Disable zoom.

    def to_csv(self, filepath, add_header):
        import io

        with io.open(filepath, 'wt', encoding='utf-8') as fd:
            chunks = iter(self._hstore.select(self._pgroup, iterator=True))
            df = next(chunks)
            df.to_csv(fd, header=add_header)

            for df in chunks:
                df.to_csv(fd, header=False)
