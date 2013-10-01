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
This module implements a buffer used to access the real data contained in
`PyTables` datasets.

By using this buffer we speed up the access to the stored data. As a
consequence, views (widgets showing a tabular representation of the dataset)
are painted much faster too.
"""

__docformat__ = 'restructuredtext'

import warnings

from PyQt4 import QtGui

import numpy
import tables

import vitables.utils


translate = QtGui.QApplication.translate
# Restrict the available flavors to 'numpy' so that reading a leaf
# always return a numpy array instead of an object of the kind indicated
# by the leaf flavor. For VLArrays the read data is returned as a list whose
# elements will be numpy arrays.
tables.restrict_flavors(keep=['numpy'])
warnings.filterwarnings('ignore', category=tables.FlavorWarning)
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)


class Buffer(object):
    """
    Buffer used to access the real data contained in `PyTables` datasets.

    Note that the buffer number of rows **must** be at least equal to the number
    of rows of the table widget it is going to fill. This way we avoid to have
    partially filled tables.
    Also note that rows in buffer are numbered from 0 to N (as it happens with
    the data source).

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

        self.data_source = leaf

        # The maximum number of rows to be read from the data source
        self.chunk_size = 10000

        # The length of the dimension that is going to be read. It
        # is an int64.
        self.leaf_numrows = self.leafNumberOfRows()
        if self.leaf_numrows <= self.chunk_size:
            self.chunk_size = self.leaf_numrows

        # The numpy array where read data will be stored
        self.chunk = numpy.array([])

        # The document row where the current chunk of data starts.
        # It must be an int64 in order to address spaces bigger than 2**32
        self.start = numpy.array(0, dtype=numpy.int64)

        # The method used for reading data depends on the kind of node.
        # Setting the reader method at initialization time increases the
        # speed of reading several orders of magnitude
        shape = leaf.shape
        if isinstance(leaf, tables.Table):
            # Dataset elements will be read like a[row][column]
            self.getCell = self.arrayCell
        elif isinstance(leaf, tables.EArray):
            self.getCell = self.EArrayCell
        elif isinstance(leaf, tables.VLArray):
            # Array elements will be read like a[row]
            self.getCell = self.vectorCell
        elif shape == ():
            # Array element will be read like a[()]
            self.getCell = self.scalarCell
        elif (len(shape) == 1):
            # Array elements will be read like a[row]
            self.getCell = self.vectorCell
        elif len(shape) > 1:
            # Dataset elements will be read like a[row][column]
            self.getCell = self.arrayCell


    def __del__(self):
        """Release resources before destroying the buffer.
        """
        self.chunk = None


    def leafNumberOfRows(self):
        """The number of rows of the dataset being read.

        We don't use the `Leaf.nrows` attribute because it is not always
        suitable for displaying the data in a 2D grid. Instead we use the
        `Leaf.shape` attribute and map it to a number of rows useful for our
        purposes.

        The returned number of rows may differ from that returned by the
        `nrows` attribute in scalar arrays and `EArrays`.

        :Returns: the size of the first dimension of the document
        """

        shape = self.data_source.shape
        if shape == None:
            # Node is not a Leaf or there was problems getting the shape
            nrows = 0
        elif shape == ():
            # Node is a rank 0 array (e.g. numpy.array(5))
            nrows = 1
        elif isinstance(self.data_source, tables.EArray):
            # Warning: the number of rows of an EArray, ea, can be different
            # from the number of rows of the numpy array ea.read()
            nrows = self.data_source.shape[0]
        else:
            nrows = self.data_source.nrows

        return numpy.array(nrows, dtype=numpy.int64)


    def getReadParameters(self, start, buffer_size):
        """
        Returns acceptable parameters for the read method.

        :Parameters:

        - `start`: the document row that is the first row of the chunk.
          It *must* be a 64 bits integer.
        - `buffer_size`: the buffer size, i.e. the number of rows to be read.

        :Returns:
            a tuple with tested values for the parameters of the read method
        """

        first_row = numpy.array(0, dtype=numpy.int64)
        last_row = self.leaf_numrows

        # When scrolling up we must keep start value >= first_row
        if start <  first_row:
            start = first_row

        # When scrolling down we must keep stop value <= last_row
        stop = start + buffer_size
        if stop > last_row:
            stop = last_row

        # Ensure that the whole buffer will be filled
        if stop - start < self.chunk_size:
            start = stop - self.chunk_size

        return start, stop


    def isDataSourceReadable(self):
        """Find out if the dataset can be read or not.

        This is not a complex test. It simply try to read a small chunk
        of data at the beginning of the dataset. If it cannot then the
        dataset is considered unreadable.
        """

        readable = True
        start, stop = self.getReadParameters(\
                            numpy.array(0, dtype=numpy.int64), self.chunk_size)
        try:
            self.data_source.read(start, stop)
        except tables.HDF5ExtError:
            readable = False
            print(translate('Buffer',
                """\nError: problems reading records. The dataset seems """
                """to be compressed with the {0} library. Check that it """
                """is installed in your system, please.""",
                'A dataset readability error').\
                format(self.data_source.filters.complib))

        return readable


    def readBuffer(self, start, buffer_size):
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

        - `start`: the document row that is the first row of the chunk.
          It *must* be a 64 bits integer.
        - `buffer_size`: the buffer size, i.e. the number of rows to be read.
        """

        start, stop = self.getReadParameters(start, buffer_size)
        try:
            # data_source is a tables.Table or a tables.XArray
            # but data is a numpy array
            # Warning: in a EArray with shape (2,3,3) and extdim attribute
            # being 1, the read method will have 3 rows. However, the numpy
            # array returned by EArray.read() will have only 2 rows
            data = self.data_source.read(start, stop)
        except tables.HDF5ExtError:
            print(translate('Buffer',
                """\nError: problems reading records. The dataset maybe """
                """corrupted.""",
                'A dataset readability error'))
        except:
            vitables.utils.formatExceptionInfo()
        else:
            # Update the buffer contents and its start position
            self.chunk = data
            self.start = start


    def scalarCell(self, row, col):
        """
        Returns a cell of a scalar array view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:

        - `row`: the row to which the cell belongs. It is a 64 bits integer
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        try:
            return self.chunk[()]
        except IndexError:
            print(u'IndexError! buffer start: {0} row, column: {1}, {2}'.\
                format(self.start, row, col))


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

        - `row`: the row to which the cell belongs. It is a 64 bits integer
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # We must shift the row value by self.start units in order to
        # get the right chunk element. Note that indices of chunk
        # needn't to be int64 because they are indexing a fixed size,
        # small chunk of data (see ctor docstring).
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        try:
            return self.chunk[int(row - self.start)]
        except IndexError:
            print(u'IndexError! buffer start: {0} row, column: {1}, {2}'.\
                  format(self.start, row, col))


    def EArrayCell(self, row, col):
        """
        Returns a cell of a EArray view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:

        - `row`: the row to which the cell belongs. It is a 64 bits integer
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # We must shift the row value by self.start units in order to
        # get the right chunk element. Note that indices of chunk
        # needn't to be int64 because they are indexing a fixed size,
        # small chunk of data (see ctor docstring).
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        # TODO: this method should be improved as it requires to read the
        # whola array keeping the read data in memory
        try:
            return self.data_source.read()[int(row - self.start)]
        except IndexError:
            print(u'IndexError! buffer start: {0} row, column: {1}, {2}'.\
                  format(self.start, row, col))


    def arrayCell(self, row, col):
        """
        Returns a cell of a ND-array view or a table view.

        The indices values are not checked (and could not be in the
        buffer) so they should be checked by the caller methods.

        :Parameters:

        - `row`: the row to which the cell belongs. It is a 64 bits integer
        - `col`: the column to wich the cell belongs

        :Returns: the cell at position `(row, col)` of the document
        """

        # We must shift the row value by self.start units in order to get the
        # right chunk element. Note that indices of chunk needn't to be
        # int64 because they are indexing a fixed size, small chunk of
        # data (see ctor docstring).
        # For arrays we have
        # chunk = [row0, row1, row2, ..., rowN]
        # and columns can be read from a given row using indexing notation
        # For tables we have
        # chunk = [nestedrecord0, nestedrecord1, ..., nestedrecordN]
        # and fields can be read from nestedrecordJ using indexing notation
        try:
            return self.chunk[int(row - self.start)][col]
        except IndexError:
            print(u'IndexError! buffer start: {0} row, column: {1}, {2}'.\
                format(self.start, row, col))
