"""This program creates a big table for tests purposes.

The program is based on the tutorial programs included in the PyTables
User's Guide.

Modified to use buffers so that filling times are bettered by one order of
magnitude. F. Altet 2006-02-27
"""
import time
from numpy import arange
from tables import *

t0 = time.time()

# Describe a particle record
class Particle(IsDescription):
    lati        = IntCol(pos=0)
    longi       = IntCol(pos=1)
    temperature = FloatCol(pos=2)
    pressure    = FloatCol(pos=3)

# Open a file in "w"rite mode
fileh = openFile("large_table.h5", mode = "w")

# Get the HDF5 root group
root = fileh.root
# Create a group
group = fileh.createGroup(root, "Particles")

# Now, create and fill the tables in Particles group
filters = Filters(complevel=1, complib='lzo', shuffle=1)
nrows = 10**7
table = fileh.createTable("/Particles", "TParticle", Particle,
                          "Sample set of particles ", filters,
                          expectedrows = nrows)

# Number of rows in buffer
nrowsbuf = 10000
# Fill the table with 10**N particles
for i in xrange(0, nrows, nrowsbuf):
    if i+nrowsbuf > nrows:
        nrapp = nrows-i
    else:
        nrapp = nrowsbuf
    # First, assign the values to the Particle record
    lati = arange(i, i+nrapp)
    longi = 10 - lati
    temperature = lati + 0.5
    pressure = 10.5 - lati
    # This injects the Record values
    table.append([lati, longi, temperature, pressure])

# Flush the table buffers and close the file
fileh.close()

tsec = round((time.time()-t0), 3)
print 'Last of the run: %s s' % (tsec)
