# This is meant to exercise ViTables capability to zoom into
# multidimensional cells.
# It also works to check views of multidimensional attributes.

from tables import *
import numpy
import numarray.strings

class Particle(IsDescription):
    name = StringCol(16, pos=1)
    lati = IntCol(pos=2)
    vector = Int32Col(shape=(200,), pos=3)
    matrix1 = Int32Col(shape=(2, 200), pos=4)
    matrix2 = FloatCol(shape=(100, 2), pos=5)
    # If the column below is uncommented, ViTables loops forever
    # when trying to visualize them
    matrix3 = FloatCol(shape=(10, 100, 2), pos=5)
    # Ideally, ViTables should be able to show even the one below
    matrix4 = FloatCol(shape=(2, 10, 100, 2), pos=5)

# Open a file in "w"rite mode
fileh = openFile("MDobjects.h5", mode = "w")
# Create the table with compression 'on' in order to reduce size as
# much as possible
table = fileh.createTable(fileh.root, 'table', Particle, "A table",
                          filters=Filters(complevel=1))
# Append several rows with default values
for i in range(10):
    table.row.append()
table.flush()

# create new arrays
atom1 = IntAtom()
shape1=(2, 10, 10, 1)
filters1 = Filters(complevel=1)
#(2, 10, 10, 3)
array1 = fileh.createCArray(fileh.root, 'array1', atom1, shape1, filters=filters1)
atom2 = FloatAtom()
shape2=(2, 10, 10, 3, 1)
filters2 = Filters(complevel=1)
#(2, 10, 10, 3, 200)
array2 = fileh.createCArray(fileh.root, 'array2', atom2, shape2, filters=filters2)

# Add multimensional attributes to the objects
# Integers will go in /table
table.attrs.MD1 = numpy.arange(5, dtype="int8")
table.attrs.MD2 = numpy.arange(10, dtype="int64").reshape(2,5)

# Complex will go in /array1
array1.attrs.MD1 = numpy.arange(5, dtype="complex128")
array1.attrs.MD2 = numpy.arange(10, dtype="complex128").reshape(2,5)

# Strings will go in /array2
array2.attrs.MD1 = numpy.array(['Hi', 'world!'], dtype='|S6')
array2.attrs.MD2 = numpy.array([['Hi', 'world!'],
                                           ['Hola', 'mon!']], dtype='|S4')

fileh.close()
