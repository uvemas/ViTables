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
#
#       This script is based on a set of scripts by Francesc Alted.

"""Several simple Arrays."""

import numpy
import tables

# Open a new empty HDF5 file
fileh = tables.openFile("array_samples.h5", mode = "w")
# Get the root group
root = fileh.root

# Create an Array
a = numpy.array([-1, 2, 4], numpy.int16)
# Save it on the HDF5 file
hdfarray = fileh.createArray(root, 'array_int16', a, "Signed short array")

# Create a scalar Array
a = numpy.array(4, numpy.int16)
# Save it on the HDF5 file
hdfarray = fileh.createArray(root, 'scalar_array', a, 
    "Scalar signed short array")

# Create a 3-d array of floats
a = numpy.arange(120, dtype=numpy.float64).reshape(20, 3, 2)
# Save it on the HDF5 file
hdfarray = fileh.createArray(root, 'array_f3D', a, "3-D float array")

# Create an array of floats
a = numpy.array([1, 2.7182818284590451, 3.141592], numpy.float)
# Save it on the HDF5 file
hdfarray = fileh.createArray(root, 'array_f', a, "Float array")

# Create a large array
#a = reshape(array(range(2**16), "s"), (2,) * 16)
a = numpy.ones((2,) * 8, numpy.int8)

# Save it on the HDF5 file
hdfarray = fileh.createArray(root, 'array_int8', a, "Large array")

# Create a set of arrays and save them on the HDF5 file
basedim = 4
group = root
dtypes = [numpy.int8, numpy.uint8, numpy.int16, numpy.int, numpy.float32, 
    numpy.float]
i = 1
for dtype in dtypes:
    # Create an array of dtype, with incrementally bigger ranges
    a = numpy.ones((basedim,) * i, dtype)
    # Save it on the HDF5 file
    dsetname = 'array_' + a.dtype.char
    hdfarray = fileh.createArray(group, dsetname, a, "Large array")
    # Create a new group
    group = fileh.createGroup(root, 'group' + str(i))
    # increment the range for next iteration
    i += 1

# Close the file
fileh.close()

