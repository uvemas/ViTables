# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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

"""Table with time fields."""

import os
import time
import numpy

import tables

# Describe a particle record
class Particle(tables.IsDescription):
    """This class defines a table record.
    """

    lati        = tables.IntCol(pos=0)
#    longi       = IntCol(pos=1)
    Time        = tables.Time64Col(pos=2)
    pressure    = tables.FloatCol(pos=3)
    ID          = tables.StringCol(itemsize=10, pos=4)
    Int16       = tables.UIntCol(itemsize=4, pos=5)
    Int64       = tables.IntCol(itemsize=8, pos=6)
    Bool        = tables.BoolCol(pos=7)

output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

# Open a new empty HDF5 file
hdf5_name = "table_ts.h5"
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
h5file = tables.openFile(filepath_hdf5, mode="w",
title='Example Table with time series')

# Get the HDF5 root group
root = h5file.root
group = h5file.createGroup(root, "Particles")
filters = tables.Filters(complevel=1, complib='lzo', shuffle=1)
nrows = 6000
table = h5file.createTable("/Particles", "TParticle", Particle,
                          "Sample set of particles ", filters,
                          expectedrows = nrows)

# Number of rows in buffer
nrowsbuf = 1000
# Fill the table with 10**N particles
for i in numpy.arange(0, nrows, nrowsbuf, dtype=numpy.int64):
    if i+nrowsbuf > nrows:
        nrapp = nrows-i
    else:
        nrapp = nrowsbuf
    # First, assign the values to the Particle record
    Int64 = numpy.arange(i, i+nrapp)
    Time = Int64 + time.time()
    lati = Int64
    pressure = lati - 10.4
    ID = (i + Int64).astype('S10')
    Int16 = lati - 50
    Bool = lati % 3 > 1
    # This injects the Record values
    table.append([lati, Time, pressure, ID, Int16, Int64, Bool])

# Flush the table buffers and close the file
h5file.close()
