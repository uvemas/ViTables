#!/usr/bin/env python3

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2019 Vicent Mas. All rights reserved
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

"""Create a PyTables file for testing purposes."""

import tables
from tables.nodes import filenode


class Particle(tables.IsDescription):
    """Description of a table record.
    """
    name        = tables.StringCol(16, pos=1)   # 16-character String
    lati        = tables.Int32Col(pos=2)        # integer
    longi       = tables.Int32Col(pos=3)        # integer
    pressure    = tables.Float32Col(pos=4)      # float  (single-precision)
    temperature = tables.Float64Col(pos=5)      # double (double-precision)

# Create a file in write mode
h5file = tables.open_file('testfile.h5', 'w')

# Create a table
root = h5file.root
group = h5file.create_group(root, "tables")
table = h5file.create_table(group, 'Particles', Particle, "A table", tables.Filters(1))

# Fill the table with 10 particles
particle = table.row
for i in range(10):
    # First, assign the values to the Particle record
    particle['name']  = f'Particle: {i:6d}'
    particle['lati'] = i
    particle['longi'] = 10 - i
    particle['pressure'] = float(i*i)
    particle['temperature'] = float(i**2)
    # This injects the row values.
    particle.append()

# We need to flush the buffers in table in order to get an
# accurate number of records on it.
table.flush()

# Create a filenode
fnode = filenode.new_node(h5file, where='/', name='filenode')

# Fill the filenode
counter = 0
while counter < 10:
    line = f"This is a line inserted programmatically at position {counter}\n"
    fnode.write(line.encode("utf-8"))
    counter += 1
fnode.write(bytearray("This is the last line.\n", "utf-8"))
fnode.attrs.author = "Vicent Mas"
fnode.close()

h5file.close()
