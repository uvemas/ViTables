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

"""
This is meant to exercise ViTables capability to zoom into
multidimensional cells.
It also works to check views of multidimensional attributes.
"""

import tables
import numpy

class Particle(tables.IsDescription):
    """Description of a table record."""
    name = tables.StringCol(16, pos=1)
    lati = tables.IntCol(pos=2)
    vector = tables.Int32Col(shape=(200,), pos=3)
    matrix1 = tables.Int32Col(shape=(2, 200), pos=4)
    matrix2 = tables.FloatCol(shape=(100, 2), pos=5)
    matrix3 = tables.FloatCol(shape=(10, 100, 2), pos=5)
    matrix4 = tables.FloatCol(shape=(2, 10, 100, 2), pos=5)

# Open a file in "w"rite mode
fileh = tables.openFile("MDobjects.h5", mode = "w")
# Create the table with compression 'on' in order to reduce size as
# much as possible
table = fileh.createTable(fileh.root, 'table', Particle, "A table", 
    filters=tables.Filters(complevel=1))
# Append several rows with default values
for i in range(10):
    table.row.append()
table.flush()

# create new arrays
atom1 = tables.IntAtom()
shape1 = (2, 10, 10, 1)
filters1 = tables.Filters(complevel=1)
#(2, 10, 10, 3)
array1 = fileh.createCArray(fileh.root, 'array1', atom1, shape1, 
    filters=filters1)
atom2 = tables.FloatAtom()
shape2 = (2, 10, 10, 3, 1)
filters2 = tables.Filters(complevel=1)
#(2, 10, 10, 3, 200)
array2 = fileh.createCArray(fileh.root, 'array2', atom2, shape2, 
    filters=filters2)

# Add multimensional attributes to the objects
# Integers will go in /table
table.attrs.MD1 = numpy.arange(5, dtype="int8")
table.attrs.MD2 = numpy.arange(10, dtype="int64").reshape(2, 5)

# Complex will go in /array1
array1.attrs.MD1 = numpy.arange(5, dtype="complex128")
array1.attrs.MD2 = numpy.arange(10, dtype="complex128").reshape(2, 5)

# Strings will go in /array2
array2.attrs.MD1 = numpy.array(['Hi', 'world!'], dtype='|S6')
array2.attrs.MD2 = numpy.array([['Hi', 'world!'], 
    ['Hola', 'mon!']], dtype='|S4')

fileh.close()
