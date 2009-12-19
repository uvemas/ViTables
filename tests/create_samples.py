import sys
import numpy
import tables

# The top level description of a sample table
class Particle(tables.IsDescription):
    name        = tables.StringCol(16, pos=1)   # 16-character String
    lati        = tables.IntCol(pos=2)        # integer
    longi       = tables.IntCol(pos=3)        # integer
    pressure    = tables.Float32Col(pos=4)    # float  (single precision)
    temperature = tables.FloatCol(pos=5)      # double (double precision)

# Define a nested field using a IsDescription descendant
class Info(tables.IsDescription):
    """A substructure of ComplexObject.
    """
    name    = tables.StringCol(16, pos=0)
    value   = tables.IntCol()
    
# Define a nested field using a dictionary
Coord = {
    "x": tables.FloatCol(pos=0),
    "y": tables.FloatCol(pos=1),
    "z": tables.FloatCol(pos=2)}

# The top level description of another sample table
# Dictionaries have an advantage over IsDescription: they allow for
# fields with blanks in their names
ComplexObject = {
    "ID": tables.StringCol(8, pos=0),   # 8-character String
    "long_ID": tables.StringCol(16, pos=1),   # 16-character String
    "position": tables.IntCol(shape=2, pos=2),        # integer
    "imag": tables.ComplexCol(16, pos=3), # complex (double precision)
    "info": Info(),
    "coord": Coord}

f = tables.openFile('samples.h5', 'w')
gts = f.createGroup(f.root, 'table_samples', 'A set of table samples')
inner_gts = f.createGroup(gts, 'inner_tables_group', '')
gas = f.createGroup(f.root, 'array_samples', 'A set of array samples')
gas._v_attrs.abstract = 'This is a group node.'

# A scalar numpy array
#<DND vmas 03-08-2007>
# Currently there is a bug in PyTables 2.x that causes it to fail operating
# with numpy scalar arrays if tables.restrict_flavors(keep=['numpy'])
# is called (which is the default behavior of ViTables). As a consequence
# tests involving file copies fail.
#</DND>
sna = numpy.array(5)
f.createArray(gas, 'sna', sna, 'A scalar numpy')

# A regular numpy array with one row
a = numpy.array([1, 2, 3], dtype=numpy.int16)
f.createArray(gas, 'a', a, 'A one row regular numpy')

# A regular numpy with more than one column
a = numpy.array([[1, 2, 3], [4, 5, 6]], numpy.float32)
f.createArray(gas, 'b', a, 'A regular numpy')

# An enlargeable array with two columns [[c1, c2] *n]
atom = tables.IntAtom()  # The object type
earray = f.createEArray(gas, 'earray', atom, (0, 2), "Enlargeable array of Ints")
# Now we enlarge the array by adding rows of fixed length. We can add
# several rows at a time
earray.append([[1, 2]])  # Append one row
earray.append([[3, 4], [5, 6]])  # Append two more rows
earray.append([[0, 1], [2, 3], [3, 4]])  # Append three more rows

# A variable length array
atom = tables.Int64Atom(shape=(2,))  # The object type
vlarray = f.createVLArray(gas, 'vlarray', atom, "Variable length array of Int64")
# Now we enlarge the array by adding rows of variable length. Only one
# row can be appended at a time
vlarray.append([1, 2])  # Row length is 2
vlarray.append(numpy.array([[3, 4, 5 ,6]]).reshape(2, 2))  # Row length is 4
vlarray.append(numpy.array([[1, 2], [3, 4], [5, 6]]))  # Row length is 6

# A table
t1 = f.createTable(inner_gts, 'inner_table', Particle, 'A table',
tables.Filters(1))
particle = t1.row
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

t2 = f.createTable(gts, 'nested_table', ComplexObject, 'A nested table',
tables.Filters(1))
cobject = t2.row
# Fill the table with 10 particles
for i in xrange(10):
    # First, assign the values to the ComplexObject record
    cobject['ID']  = 'OID: %3d' % (i)
    cobject['long_ID']  = 'Long ID: %6d' % (i)
    cobject['position'] = (i, i+1)
    cobject['imag'] = complex(i, 2*i)
    cobject['info/name'] = 'Name: %6d' % (i)
    cobject['info/value'] = i
    cobject['coord/x'] = float(i**2)
    cobject['coord/y'] = float(1+i**2)
    cobject['coord/z'] = float(2+i**2)
    # This injects the row values.
    cobject.append()

# An empty table
t3 = f.createTable(gts, 'empty_table', Particle, 'An empty table')

# We need to flush the buffers in table in order to get an
# accurate number of records on it.
t1.flush()
t2.flush()
t3.flush()

f.close()
