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

"""Several simple Tables."""

import sys

import numpy
import tables

class Particle(tables.IsDescription):
    """Description of a table record.
    """
    name        = tables.StringCol(16, pos=1)   # 16-character String
    lati        = tables.Int32Col(pos=2)        # integer
    longi       = tables.Int32Col(pos=3)        # integer
    pressure    = tables.Float32Col(pos=4)      # float  (single-precision)
    temperature = tables.Float64Col(pos=5)      # double (double-precision)

# Open a file in "w"rite mode
fileh = tables.openFile("table_samples.h5", mode = "w")

root = fileh.root
# Create a new group
group = fileh.createGroup(root, "newgroup")

# Create a new table in newgroup group
table = fileh.createTable(group, 'table', Particle, "A table", 
    tables.Filters(1))
particle = table.row

# Fill the table with 10 particles
for i in xrange(10):
    # First, assign the values to the Particle record
    particle['name']  = 'Particle: %6d' % (i)
    particle['lati'] = i
    particle['longi'] = 10 - i
    particle['pressure'] = float(i*i)
    particle['temperature'] = float(i**2)
    # This injects the row values.
    particle.append()

# We need to flush the buffers in table in order to get an
# accurate number of records on it.
table.flush()

# Add a couple of user attrs
table.attrs.user_attr1 = 1.023
table.attrs.user_attr2 = "This is the second user attr"

# Append several rows in only one call
table.append([("Particle:     10", 10, 0, 10*10, 10**2),
              ("Particle:     11", 11, -1, 11*11, 11**2),
              ("Particle:     12", 12, -2, 12*12, 12**2)])
table.flush()

class Particle2(tables.IsDescription):
    """Description of a table record.
    """
    name        = tables.StringCol(16, pos=1)   # 16-character String
    lati        = tables.ComplexCol(itemsize=16, pos=2)
    longi       = tables.ComplexCol(itemsize=8, pos=3)
    vector      = tables.ComplexCol(itemsize=8, shape=(2,), pos=4)
    matrix2D    = tables.ComplexCol(itemsize=16, shape=(2, 2), pos=5)

# Open a file in "w"rite mode
table1 = fileh.createTable(root, 'table1', Particle2, "A table")
# Append several rows in only one call
table1.append([("Particle:     10", 10j, 0, (10*9+1j, 1), [[10**2j, 11*3]]*2),
              ("Particle:     11", 11j, -1, (11*10+2j, 2), [[11**2j, 10*3]]*2),
              ("Particle:     12", 12j, -2, (12*11+3j, 3), [[12**2j, 9*3]]*2),
              ("Particle:     13", 13j, -3, (13*11+4j, 4), [[13**2j, 8*3]]*2),
              ("Particle:     14", 14j, -4, (14*11+5j, 5), [[14**2j, 7*3]]*2)])
table1.flush()

######
class Particle3(tables.IsDescription):
    ADCcount    = tables.Int16Col()              # signed short integer
    TDCcount    = tables.UInt8Col()              # unsigned byte
    grid_i      = tables.Int32Col()              # integer
    grid_j      = tables.Int32Col()              # integer
    idnumber    = tables.Int64Col()              # signed long long
    name        = tables.StringCol(16, dflt="")  # 16-character String
    pressure    = tables.Float32Col(shape=2)     # float  (single-precision)
    temperature = tables.Float64Col()            # double (double-precision)

Particle4 = {
    # You can also use any of the atom factories, i.e. the one which
    # accepts a PyTables type.
    "ADCcount"    : tables.Col.from_type("int16"),    # signed short integer
    "TDCcount"    : tables.Col.from_type("uint8"),    # unsigned byte
    "grid_i"      : tables.Col.from_type("int32"),    # integer
    "grid_j"      : tables.Col.from_type("int32"),    # integer
    "idnumber"    : tables.Col.from_type("int64"),    # signed long long
    "name"        : tables.Col.from_kind("string", 16),  # 16-character String
    "pressure"    : tables.Col.from_type("float32", (2,)), # float  (single-precision)
    "temperature" : tables.Col.from_type("float64"),  # double (double-precision)
}

# Create a new group under "/" (root)
group = fileh.createGroup("/", 'detector')

# Create one table on it
#table = h5file.createTable(group, 'table', Particle, "Title example")
# You can choose creating a Table from a description dictionary if you wish
table2 = fileh.createTable(group, 'table', Particle4, "Title example")

# Create a shortcut to the table record object
particle = table2.row

# Fill the table with 10 particles
for i in xrange(10):
    # First, assign the values to the Particle record
    particle['name']  = 'Particle: %6d' % (i)
    particle['TDCcount'] = i % 256
    particle['ADCcount'] = (i * 256) % (1 << 16)
    particle['grid_i'] = i
    particle['grid_j'] = 10 - i
    particle['pressure'] = [float(i*i), float(i*2)]
    particle['temperature'] = float(i**2)
    particle['idnumber'] = i * (2 ** 34)  # This exceeds integer range
    # This injects the Record values.
    particle.append()

# Flush the buffers for table
table2.flush()

# Create a new group to hold new arrays
gcolumns = fileh.createGroup("/", "columns")
pressure = [ p['pressure'] for p in table2.iterrows() ]
# Create an array with this info under '/columns' having a 'list' flavor
fileh.createArray(gcolumns, 'pressure', pressure, 
                   "Pressure column")

# Do the same with TDCcount, but with a numpy object
TDC = [ p['TDCcount'] for p in table2.iterrows() ]
fileh.createArray('/columns', 'TDC', numpy.array(TDC), "TDCcount column")

# Do the same with name column
names = [ p['name'] for p in table2.iterrows() ]
fileh.createArray('/columns', 'name', names, "Name column")

# Save a recarray object under detector
r = numpy.rec.array("a"*300, formats='f4,3i4,a5,i2', shape=3)
recarrt = fileh.createTable("/detector", 'recarray', r, "RecArray example")
r2 = r[0:3:2]
# Change the byteorder property
recarrt = fileh.createTable("/detector", 'recarray2', r2,
                             "Non-contiguous recarray")

# Finally, append some new records to table
table3 = fileh.root.detector.table

# Append 5 new particles to table (yes, tables can be enlarged!)
particle = table3.row
for i in xrange(10, 15):
    # First, assign the values to the Particle record
    particle['name']  = 'Particle: %6d' % (i)
    particle['TDCcount'] = i % 256
    particle['ADCcount'] = (i * 256) % (1 << 16)
    particle['grid_i'] = i
    particle['grid_j'] = 10 - i
    particle['pressure'] = [float(i*i), float(i*2)]
    particle['temperature'] = float(i**2)
    particle['idnumber'] = i * (2 ** 34)  # This exceeds integer range
    # This injects the Row values.
    particle.append()

# Flush this table
table3.flush()

# Finally, close the file
fileh.close()
