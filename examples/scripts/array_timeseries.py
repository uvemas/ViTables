# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""CArray with time fields.
"""

import os
import time

import tables

output_dir = '../timeseries'
try:
    os.mkdir(output_dir)
except OSError:
    pass

# Open a new empty HDF5 file
hdf5_name = "carray_ts.h5"
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
h5file = tables.openFile(filepath_hdf5, mode="w",
title='Example CArray with time fields')

# Create a CArray and fill it
root = h5file.root
shape = (300, 2)
atom = tables.Time32Atom()
filters = tables.Filters(complevel=5, complib='zlib')
hdfarray = h5file.createCArray(root, 'test_carray_1', atom, shape, 
    "Signed short array")
now = time.time()
seconds_by_day = 1*24*60*60
for index in range(0, 600, 2):
    seconds = now - seconds_by_day * index 
    hdfarray[index/2, 0] = seconds
    hdfarray[299-index/2, 1] = seconds

# Create other CArray and fill it
shape = (300,)
atom = tables.Time32Atom(shape=(2,))
filters = tables.Filters(complevel=5, complib='zlib')
hdfarray = h5file.createCArray(root, 'test_carray_2', atom, shape, 
    "Signed short array")
now = time.time()
seconds_by_day = 1*24*60*60
for index in range(0, 600, 2):
    seconds = now - seconds_by_day * index 
    hdfarray[index/2] = [seconds, seconds]

h5file.close()
