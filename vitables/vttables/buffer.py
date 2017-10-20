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
This module implements a buffer used to access the real data contained in
`PyTables` datasets.
By using this buffer we speed up the access to the stored data. As a
consequence, views (widgets showing a tabular representation of the dataset)
are painted much faster too.
"""

import logging
import warnings

import numpy
import tables

from qtpy import QtWidgets

from .. import utils as vtutils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# Restrict the available flavors to 'numpy' so that reading a leaf
# always return a numpy array instead of an object of the kind indicated
# by the leaf flavor. For VLArrays the read data is returned as a list whose
# elements will be numpy arrays.
tables.restrict_flavors(keep=['numpy'])
warnings.filterwarnings('ignore', category=tables.FlavorWarning)
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

log = logging.getLogger(__name__)


class Buffer(object):
    """Buffer used to access the real data contained in `PyTables` datasets.

    Note that the buffer number of rows **must** be at least equal to
    the number of rows of the table widget it is going to fill. This
    way we avoid to have partially filled tables.  Also note that rows
    in buffer are numbered from 0 to N (as it happens with the data
    source).

    Leaves are displayed in MxN table widgets:
    - scalar arrays are displayed in a 1x1 table.
    - 1D arrays are displayed in a Mx1 table.
    - KD arrays are displayed in a MxN table.
    - tables are displayed in a MxN table with one field per column

    Implementing a reader method for each case allows us to choose
    at document creation time which method will be used. It works
    *much* faster than a global reader method that has to decide
    which block of code must be executed at every cell painting time.

    :Parameter leaf:
        the data source (`tables.Leaf` instance) from which data are
        going to be read.
    """

    def __init__(self, leaf):
        """
        Initializes the buffer.
        """

        self.leaf = leaf
        # The structure where read data will be stored.
        self.chunk = numpy.array([])

        # The method used for reading data depends on the kind of node.
        # Setting the reader method at initialization time increases the
        # speed of reading several orders of magnitude
        if isinstance(leaf, tables.Table):
            # Dataset elements will be read like a[row][column]
            self.getCell = self.arrayCell
        elif isinstance(leaf, tables.EArray):
            self.getCell = self.EArrayCell
        elif isinstance(leaf, tables.VLArray):
            # Array elements will be read like a[row]
            self.getCell = self.vectorCell
        elif leaf.shape == ():
            # Array element will be read like a[()]
            self.getCell = self.scalarCell
        elif len(leaf.shape) == 1:
            # Array elements will be read like a[row]
            self.getCell = self.vectorCell
        elif len(leaf.shape) > 1:
            # Dataset elements will be read like a[row][column]
            self.getCell = self.arrayCell

    def __del__(self):
        """Release resources before destroying the buffer.
        """
        # FIXME: PY3.5+ leaks resources (use finalizer instead).
        self.chunk = None

    def total_nrows(self):
        """Estimates the number of rows of the dataset being read.

        We don't use the `Leaf.nrows` attribute because it is not always
        suitable for displaying the data in a 2D grid. Instead we use the
        `Leaf.shape` attribute and map it to a number of rows useful for our
        purposes.

        The returned number of rows may differ from that returned by the
        `nrows` attribute in scalar arrays and `EArrays`.

        :Returns: the size of the first dimension of the dataset
        """

        shape = self.leaf.shape
        if shape is None:
            # Node is not a Leaf or there was problems getting the shape
            nrows = 0
        elif shape == ():
            # Node is a rank 0 array (e.g. numpy.array(5))
            nrows = 1
        else:
            nrows = self.leaf.nrows

        return nrows

    def readBuffer(self, start, stop):
        """
        Read a chunk from the data source.

        The size of the chunk is given in number of rows, and might
        be smaller than the requested one if the beginning/end of the
        document is reached when reading.

        Data read from `VLArrays` are returned as a Python list of objects of
        the current flavor (usually ``numpy`` arrays). Any
        other kind of `tables.Leaf` returns a ``numpy`` array (see comments on
        restricted_flavors above)

        :Parameters:
        :param start: the document row that is the first row of the chunk.
        :param stop: the last row to read, inclusive.
        """

        try:
            # data_source is a tables.Table or a tables.XArray
            # but data is a numpy array
            # Warning: in a EArray with shape (2,3,3) and extdim attribute
            # being 1, the read method will have 3 rows. However, the numpy
            # array returned by EArray.read() will have only 2 rows
            data = self.leaf.read(start, stop)
        except tables.HDF5ExtError as e:
            log.error(
                translate('Buffer', """\nError: problems reading records. """
                          """The dataset maybe corrupted.\n{}""",
                          'A dataset readability error').format(e.message))
        except:
            vtutils.formatExceptionInfo()
        else:
            # Update the buffer contents and its start position
            self.chunk = data

    def scalarCell(self, row, col):
        """
        Returns a cell of a scalar array view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:
        - `row`: the row to which the cell belongs.
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """
        return self.chunk[()]

    def vectorCell(self, row, col):
        """
        Returns a cell of a 1D-array view.

        VLArrays, for instance, always are read with this method. If no
        pseudo atoms are used then a list of arrays is returned. If vlstring
        is used then a list of raw bytes is returned. If vlunicode is used
        then a list of unicode strings is returned. If object is used then a
        list of Python objects is returned.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:
        - `row`: the row to which the cell belongs.
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # The row-coordinate must be shifted by model.start units in order to
        # get the right chunk element.
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        return self.chunk[row]

    def EArrayCell(self, row, col):
        """
        Returns a cell of a EArray view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:
        - `row`: the row to which the cell belongs.
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # The row-coordinate must be shifted by model.start units in order to
        # get the right chunk element.
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        # Get data for cell
        cell_data = numpy.take(self.chunk, [row], axis=self.leaf.maindim)
        # Remove extra dimension
        cell_data = numpy.squeeze(cell_data, axis=self.leaf.maindim)
        return cell_data

    def arrayCell(self, row, col):
        """
        Returns a cell of a ND-array view or a table view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:
        - `row`: the row to which the cell belongs.
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # The row-coordinate must be shifted by model.start units in order to
        # get the right chunk element.
        # For arrays we have
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        # For tables we have
        # chunk = [nestedrecord0, nestedrecord1, ..., nestedrecordN]
        # and fields can be read from nestedrecordJ using indexing notation
        return self.chunk[row][col]
