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

"""This program creates a potentially big table for tests purposes.

The program is based on the tutorial programs included in the PyTables
User's Guide.

Modified to use buffers so that filling times are bettered by one order of
magnitude. F. Altet 2006-02-27
"""

import time
from numpy import arange
import tables

t0 = time.time()

# Describe a particle record
class Particle(tables.IsDescription):
    """Description of a table record."""
    lati        = tables.IntCol(pos=0)
    longi       = tables.IntCol(pos=1)
    temperature = tables.FloatCol(pos=2)
    pressure    = tables.FloatCol(pos=3)

# Open a file in "w"rite mode
fileh = tables.openFile("large_table.h5", mode = "w")

# Get the HDF5 root group
root = fileh.root
# Create a group
group = fileh.createGroup(root, "Particles")

# Now, create and fill the tables in Particles group
filters = tables.Filters(complevel=1, complib='lzo', shuffle=1)
nrows = 10**7
table = fileh.createTable("/Particles", "TParticle", Particle, 
    "Sample set of particles ", filters, expectedrows = nrows)

# Number of rows in buffer
nrowsbuf = 10000
# Fill the table with 10**N particles
for i in xrange(0, nrows, nrowsbuf):
    if i + nrowsbuf > nrows:
        nrapp = nrows - i
    else:
        nrapp = nrowsbuf
    # First, assign the values to the Particle record
    lati = arange(i, i + nrapp)
    longi = 10 - lati
    temperature = lati + 0.5
    pressure = 10.5 - lati
    # This injects the Record values
    table.append([lati, longi, temperature, pressure])

# Flush the table buffers and close the file
fileh.close()

tsec = round((time.time() - t0), 3)
print 'Last of the run: %s s' % (tsec)
