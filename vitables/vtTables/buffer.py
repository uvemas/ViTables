# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
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
#       $Id: buffer.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the Buffer class.

Classes:

* Buffer

Methods:

* __init__(self, document)
* getReadParameters(self, start, bs)
* readBuffer(self, start, bs)
* scalarCell(self, row, col)
* vectorCell(self, row, col)
* arrayCell(self, row, col)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys
import warnings

import numpy
import tables

import vitables.utils

# Restrict the available flavors to 'numpy' so that reading a leaf
# always return a numpy array instead of an object of the kind indicated
# by the leaf flavor. For VLArrays the read data is returned as a list whose
# elements will be numpy arrays.
tables.restrict_flavors(keep=['numpy'])
warnings.filterwarnings('ignore', category=tables.FlavorWarning)
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

class Buffer:
    """
    Buffer used to access `ArrayDoc` and `TableDoc` instances data.

    By using this buffer the leaf view drawing speed increases sensibly.
    Note that the buffer number of rows **must** be at least equal to the number
    of rows of the table widget it is going to fill. This way we avoid to have
    partially full tables.
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
    """


    def __init__(self, document):
        """
        Reads the first chunk of data from a data source.

        The first chunk of data starts at row number 0.

        :Parameter document:
            the data source (`NodeDoc` instance) from which data are
            going to be read.
        """

        # The data source
        self.document = document

        # The document row where the buffer starts
        # It must be an int64 in order to address spaces bigger than 2**32
        self.start = numpy.array(0, dtype=numpy.int64)

        # Every chunk of data read from the data source is stored in a list
        # The maximum length of the list (i.e. the chunk size) is 10000 rows
        self.chunk = []
        self.chunkSize = 10000

        # Set the length of the dimension that is going to be read. It
        # is an int64.
        # For Arrays see ArrayDoc.numRows() to see how it differs from
        # the view number of rows
        self.dimLength = self.document.node.nrows

        # A flag for dealing with unreadable datasets
        self.unreadableDataset = False


    def getReadParameters(self, start, bs):
        """
        Returns acceptable parameters for the read method.

        :Parameters:

        - `start`: is the document row that is the first row of the chunk.
          It *must* be a 64 bits integer.
        - `bs`: is the buffer size, i.e. the number of rows to be read.

        :Returns:
            a tuple with tested values for the parameters of the read method
        """

        firstRow = numpy.array(0, dtype=numpy.int64)
        lastRow = self.dimLength

        # When scrolling up we must keep start value >= firstRow
        if start <  firstRow:
            start = firstRow

        # When scrolling down we must keep stop value <= lastRow
        stop = start + bs
        if stop > lastRow:
            stop = lastRow

        return start, stop


    def readBuffer(self, start, bs):
        """
        Read a chunk from the data source.

        The size of the chunk is given in number of rows, and might
        be smaller than the requested one if the beginning/end of the
        document is reached when reading.

        Data read from VLArrays are returned as a Python list. Any
        other kind of Leaf returns a numpy array (see comments on
        restricted_flavors above)

        :Parameters:

        - `start`: is the document row that is the first row of the chunk.
          It *must* be a 64 bits integer.
        - `bs`: is the buffer size, i.e. the number of rows to be read.
        """

        start, stop = self.getReadParameters(start, bs)
        try:
            data = self.document.node.read(start, stop)
        except tables.HDF5ExtError:
            self.unreadableDataset = True
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
        except IndexError, v:
            print 'IndexError! buffer start: %s row, column: %s, %s' % (self.start, row, col)


    def vectorCell(self, row, col):
        """
        Returns a cell of a 1D-array view.

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
        except IndexError, v:
            print 'IndexError! buffer start: %s row, column: %s, %s' % (self.start, row, col)


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
        except IndexError, v:
            print 'IndexError! buffer start: %s row, column: %s, %s' % (self.start, row, col)
