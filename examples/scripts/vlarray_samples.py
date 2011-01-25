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

"""Several simple VLArrays."""

import cPickle

import tables
import numpy

# Create a VLArray:
fileh = tables.openFile('vlarray_samples.h5', mode='w')

root = fileh.root
vlarray = fileh.createVLArray(root, 'vlarray1', 
    tables.Int32Atom(), "ragged array of ints", filters=tables.Filters(1))
# Append some (variable length) rows:
vlarray.append(numpy.array([5, 6]))
vlarray.append(numpy.array([5, 6, 7]))
vlarray.append([5, 6, 9, 8])

# Now, do the same with native Python strings.
vlarray2 = fileh.createVLArray(root, 'vlarray2', 
    tables.StringAtom(itemsize=2), "ragged array of strings", 
    filters=tables.Filters(1))
vlarray2.flavor = 'python'
# Append some (variable length) rows:
vlarray2.append(['5', '66'])
vlarray2.append(['5', '6', '77'])
vlarray2.append(['5', '6', '9', '88'])

# Test with lists of bidimensional vectors
vlarray3 = fileh.createVLArray(root, 'vlarray3', tables.Int64Atom(shape=(2,)), 
    "Ragged array of vectors")
a = numpy.array([[1, 2], [1, 2]], dtype=numpy.int64)
vlarray3.append(a)
vlarray3.append(numpy.array([[1, 2], [3, 4]], dtype=numpy.int64))
vlarray3.append(numpy.zeros(dtype=numpy.int64, shape=(0, 2)))
vlarray3.append(numpy.array([[5, 6]], dtype=numpy.int64))
# This makes an error (shape)
#vlarray.append(array([[5], [6]], dtype=int64))
# This makes an error (type)
#vlarray.append(array([[5, 6]], dtype=uint64))

# Tests with strings

# Python flavor
vlarray5 = fileh.createVLArray(root, 'vlarray5', 
    tables.StringAtom(itemsize=3),  "Ragged array of strings")
vlarray5.flavor = "python"
vlarray5.append(["123", "456", "3"])
vlarray5.append(["456", "3"])

# Binary strings
vlarray6 = fileh.createVLArray(root, 'vlarray6', tables.UInt8Atom(), 
    "pickled bytes")
data = cPickle.dumps((["123", "456"], "3"))
vlarray6.append(numpy.ndarray(buffer=data, dtype=numpy.uint8, shape=len(data)))

# The next is a way of doing the same than before
vlarray7 = fileh.createVLArray(root, 'vlarray7', tables.ObjectAtom(), 
    "pickled object")
vlarray7.append([["123", "456"], "3"])

# Boolean arrays are supported as well
vlarray8 = fileh.createVLArray(root, 'vlarray8', tables.BoolAtom(), 
    "Boolean atoms")
# The next lines are equivalent...
vlarray8.append([1, 0])
vlarray8.append([1, 0, 3, 0])  # This will be converted to a boolean
# This gives a TypeError
#vlarray.append([1,0,1])

# Variable length strings
vlarray9 = fileh.createVLArray(root, 'vlarray9', tables.VLStringAtom(), 
    "Variable Length String")
vlarray9.append("asd")
vlarray9.append("aaana")

# Unicode variable length strings
vlarray10 = fileh.createVLArray(root, 'vlarray10', tables.VLUnicodeAtom(), 
    "Variable Length Unicode String")
vlarray10.append(u"aaana")
vlarray10.append(u"")   # The empty string
vlarray10.append(u"asd")
vlarray10.append(u"para\u0140lel")

# Still more vlarrays...
N = 100
shape = (3,3)
numpy.random.seed(10)  # For reproductible results
vlarray11 = fileh.createVLArray(root, 'vlarray11', 
    tables.Float64Atom(shape=shape), "ragged array of arrays")

k = 0
for i in xrange(N):
    l = []
    for j in xrange(numpy.random.randint(N)):
        l.append(numpy.random.randn(*shape))
        k += 1
    vlarray11.append(l)

# Close the file.
fileh.close()
