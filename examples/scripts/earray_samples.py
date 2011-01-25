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

"""Several simple EArrays."""

import tables
import numpy

fileh = tables.openFile('earray_samples.h5', mode='w')

root = fileh.root
a = tables.StringAtom(itemsize=8)
# Use ``a`` as the object type for the enlargeable array.
array_c = fileh.createEArray(root, 'array_c', a, (0,), "Chars")
array_c.append(numpy.array(['a'*2, 'b'*4], dtype='S8'))
array_c.append(numpy.array(['a'*6, 'b'*8, 'c'*10], dtype='S8'))

# Create an string atom
a = tables.StringAtom(itemsize=1)
# Use it as a type for the enlargeable array
hdfarray = fileh.createEArray(root, 'array_char', a, (0,), "Character array")
hdfarray.append(numpy.array(['a', 'b', 'c']))
# The next is legal:
hdfarray.append(numpy.array(['c', 'b', 'c', 'd']))
# but these are not:
#hdfarray.append(array([['c', 'b'], ['c', 'd']]))
#hdfarray.append(array([[1,2,3],[3,2,1]], dtype=uint8).reshape(2,1,3))

# Create an atom
a = tables.UInt16Atom()
hdfarray = fileh.createEArray(root, 'array_e', a, (2, 0, 3), 
    "Unsigned short array")

# Create an enlargeable array
a = tables.UInt8Atom()
hdfarray = fileh.createEArray(root, 'array_b', a, (2, 0, 3), 
    "Unsigned byte array", tables.Filters(complevel = 1))

# Append an array to this table
hdfarray.append(numpy.array([[1, 2, 3], [3, 2, 1]], 
    dtype=numpy.uint8).reshape(2, 1, 3))
hdfarray.append(numpy.array([[1, 2, 3], [3, 2, 1], [2, 4, 6], [6, 4, 2]], 
    dtype=numpy.uint8).reshape(2,2,3)*2)
# The next should give a type error:
#hdfarray.append(array([[1,0,1],[0,0,1]], dtype=Bool).reshape(2,1,3))

# Close the file.
fileh.close()
