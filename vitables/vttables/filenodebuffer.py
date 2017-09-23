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
`PyTables` filenode.

By using this buffer we speed up the access to the stored data. As a
consequence, views (widgets showing a tabular representation of the dataset)
are painted much faster too.
"""

import logging
import warnings
import linecache

import numpy
import tables

from .. import utils as vtutils

__docformat__ = 'restructuredtext'

# Restrict the available flavors to 'numpy' so that reading a leaf
# always return a numpy array instead of an object of the kind indicated
# by the leaf flavor. For VLArrays the read data is returned as a list whose
# elements will be numpy arrays.
tables.restrict_flavors(keep=['numpy'])
warnings.filterwarnings('ignore', category=tables.FlavorWarning)
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)

log = logging.getLogger(__name__)


class FilenodeBuffer(object):
    """Buffer used to access the real data contained in `PyTables` filenode.

    Note that the buffer number of rows **must** be at least equal to
    the number of rows of the table widget it is going to fill. This
    way we avoid to have partially filled tables.  Also note that rows
    in buffer are numbered from 0 to N (as it happens with the data
    source).

    Filenodes are displayed in Mx1 table widgets.

    :Parameter leaf:
        the data source (`tables.EArray` instance) from which data are
        going to be read.
    """

    def __init__(self, leaf):
        """
        Initializes the buffer.
        """

        self.leaf = leaf
        # The structure where read data will be stored.
        self.chunk = numpy.array([])

        vtapp = vtutils.getApp()
        self.temp_filenode, self.total_rows = vtapp.filenodes_map[leaf]

    def __del__(self):
        """Release resources before destroying the buffer.
        """
        # FIXME: PY3.5+ leaks resources (use finalizer instead).
        self.chunk = None

    def total_nrows(self):
        return self.total_rows

    def readBuffer(self, start, stop):
        """
        Read the whole filenode in memory using the linecache module.
        Data is returned as a Python list of byte strings.

        :Parameters:
        :param start: the document row that is the first row of the chunk.
        :param stop: the last row to read, inclusive.
        """

        # The line numbers of files read by linecache start with 1
        if start == 0:
            start += 1
        if stop > self.total_rows:
            stop = self.total_rows

        data = []
        counter = start
        while counter <= stop:
            data.append(linecache.getline(self.temp_filenode, counter))
            counter += 1
        self.chunk = data

    def getCell(self, row, col):
        """
        Returns a cell of a 1D-array view.

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
